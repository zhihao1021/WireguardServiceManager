from aiohttp import ClientSession
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)
from jwt import encode, decode
from orjson import loads
from pydantic import BaseModel

from typing import Annotated, Optional

from config import (
    JWT_KEY,
    JOIN_KEY,
    DISCORD_REDIRECT_URI,
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET
)
from scheams.connection_info import ConnectionInfo
from scheams.jwt import JWT, JWTPayload
from scheams.user import (
    DiscordTokenData,
    DiscordUserData,
    UserData
)


class OAuthData(BaseModel):
    code: str
    join_key: Optional[str] = None


DISCORD_API = "https://discord.com/api/v10/"

AUTHORIZE_FAILED = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Authorize failed"
)
JOIN_KEY_WRONG = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="The join key is wrong"
)
INVALIDE_AUTHENTICATION_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials"
)
IP_NOT_ENOUGH = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="IP on host not enough"
)

SECURITY = HTTPBearer(
    scheme_name="JWT",
    description="JWT which get from posting discord oauth code to /oauth"
)

router = APIRouter(
    prefix="/oauth",
    tags=["OAuth"]
)


def valid_token_string(jwt: str):
    try:
        decode_data = JWTPayload(**decode(
            jwt=jwt,
            key=JWT_KEY,
            algorithms=["HS256"],
            options={
                "require": ["exp", "iat"]
            }
        ))

        return decode_data
    except:
        raise INVALIDE_AUTHENTICATION_CREDENTIALS


def valid_token(token: HTTPAuthorizationCredentials = Security(SECURITY)) -> JWTPayload:
    jwt = token.credentials
    return valid_token_string(jwt)


user_depends = Depends(valid_token)
UserDepends = Annotated[JWTPayload, user_depends]


async def fetch_user_data(token_data: DiscordTokenData) -> DiscordUserData:
    async with ClientSession(
        headers={
            "Authorization": f"{token_data.token_type} {token_data.access_token}"
        }
    ) as client:
        response = await client.get(f"{DISCORD_API}/users/@me")
        data = loads(await response.content.read())
        data["discord_id"] = data["id"]
        return DiscordUserData(
            **data
        )


async def valid_code(
    code: Optional[str] = None,
    token: Optional[str] = None,
    join_key: Optional[str] = None,
) -> UserData:
    if code is None and token is None:
        raise ValueError

    async with ClientSession(
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    ) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        } if code else {
            "grant_type": "refresh_token",
            "refresh_token": token
        }
        data["client_id"] = DISCORD_CLIENT_ID
        data["client_secret"] = DISCORD_CLIENT_SECRET

        response = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data=data
        )

        if response.status != 200:
            raise AUTHORIZE_FAILED

        token_data = DiscordTokenData(**loads(
            await response.content.read()
        ))

    if "identify" not in token_data.scope:
        raise AUTHORIZE_FAILED

    discord_data = await fetch_user_data(token_data)
    new_data = token_data.model_dump()
    new_data.update(discord_data.model_dump())

    user_data = await UserData.find_one(UserData.discord_id == discord_data.discord_id)
    if user_data is None:
        if join_key != JOIN_KEY:
            raise JOIN_KEY_WRONG

        connection = await ConnectionInfo.find_one(
            ConnectionInfo.discord_user_id == None
        )
        if connection is None:
            raise IP_NOT_ENOUGH

        user_data = UserData(
            **new_data,
            connection=connection
        )
        connection.discord_user_id = user_data.discord_id

        await connection.save()
        await user_data.save()
    else:
        await user_data.set(new_data)

    return user_data


@router.post(
    path="",
    response_model=JWT,
    status_code=status.HTTP_201_CREATED,
    description="Get token by discord code"
)
async def oauth(data: OAuthData) -> JWT:
    user_data = await valid_code(
        code=data.code,
        join_key=data.join_key
    )

    jwt_payload = JWTPayload(**user_data.model_dump())

    return JWT(
        access_token=encode(
            jwt_payload.model_dump(),
            key=JWT_KEY,
        )
    )


@router.put(
    path="",
    response_model=JWT,
    status_code=status.HTTP_200_OK,
    description="Refresh token",
)
async def refresh(user: UserDepends) -> JWT:
    user_data = await UserData.find_one(UserData.discord_id == user.discord_id)

    new_data = await valid_code(token=user_data.refresh_token)

    jwt_payload = JWTPayload(**new_data.model_dump())

    return JWT(
        access_token=encode(
            jwt_payload.model_dump(),
            key=JWT_KEY,
        )
    )
