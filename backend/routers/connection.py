from fastapi import (
    APIRouter,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from starlette.websockets import WebSocketState

from asyncio import sleep as asleep

from scheams.connection_info import ConnectionInfo
from scheams.user import (
    DiscordUserDataWithConnectionInfo,
    UserData
)
from wireguard_status import PUBLISHER

from .oauth import UserDepends, user_depends, valid_token_string


IP_NOT_ENOUGH = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="IP on host not enough"
)

router = APIRouter(
    prefix="/connection",
    tags=["Connection"]
)


@router.get(
    path="",
    response_model=list[DiscordUserDataWithConnectionInfo],
    status_code=status.HTTP_200_OK,
    dependencies=[user_depends]
)
async def get_users() -> list[DiscordUserDataWithConnectionInfo]:
    return await UserData.find(fetch_links=True).project(DiscordUserDataWithConnectionInfo).to_list()


@router.get(
    path="/connect",
    status_code=status.HTTP_200_OK
)
async def get_connection_string(user: UserDepends) -> str:
    connection_data = await ConnectionInfo.find_one(
        ConnectionInfo.discord_user_id == user.discord_id
    )

    if connection_data is None:
        return ""
    return connection_data.to_client_conf()


@router.websocket(
    path=""
)
async def subscribe(ws: WebSocket):
    try:
        await ws.accept()
        token = await ws.receive_text()
        try:
            valid_token_string(token)
        except:
            await ws.close()

        await PUBLISHER.add_subscriber(ws)
        while ws.client_state == WebSocketState.CONNECTED:
            await asleep(1)
    except WebSocketDisconnect:
        PUBLISHER.remove_subscriber(ws)
