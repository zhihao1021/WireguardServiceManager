from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field, model_validator

from typing import Annotated, Any, Optional

from .connection_info import ConnectionInfo, ConnectionInfoPublic


class DiscordTokenData(BaseModel):
    access_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 604800
    refresh_token: str = ""
    scope: str = "identify"


class DiscordUserData(BaseModel):
    discord_id: Annotated[str, Indexed(unique=True)] = Field(
        title="UserID",
        description="Discord user id.",
    )
    username: str = Field(
        title="UserName",
        description="Discord username."
    )
    global_name: Optional[str] = Field(
        default=None,
        title="UserDisplayName",
        description="Discord user's global name."
    )
    avatar: Optional[str] = Field(
        default=None,
        title="UserAvatar",
        description="URL of discord user's avatar."
    )
    display_name: str = Field(
        default="",
        title="UserDisplayName",
        description="User's display name."
    )
    display_avatar: str = Field(
        default="",
        title="UserAvatar",
        description="URL of user's avatar."
    )

    @model_validator(mode="after")
    def update_display_field(self):
        self.display_name = self.global_name or self.username
        if self.avatar:
            self.display_avatar = f"https://cdn.discordapp.com/avatars/{self.discord_id}/{self.avatar}.png"
        else:
            self.display_avatar = "https://cdn.discordapp.com/embed/avatars/0.png"

        return self


class DiscordUserDataWithConnectionInfo(DiscordUserData):
    connection: ConnectionInfoPublic


class UserData(Document, DiscordTokenData, DiscordUserData):
    connection: Link[ConnectionInfo]

    class Settings:
        name = "UserData"
