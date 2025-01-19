from beanie import Document
from pydantic import BaseModel

from typing import Optional

from config import (
    WIREGUARD_ENDPOINT,
    WIREGUARD_KEEP_ALIVE,
    WIREGUARD_PUBLIC_KEY,
    WIREGUARD_PRESHARED_KEY,
    WIREGUARD_SUBNET,
)


class ConnectionInfo(Document):
    private_key: str
    public_key: str
    ip_address: str
    discord_user_id: Optional[str] = None

    def to_client_conf(self) -> str:
        result = [
            f"[Interface]",
            f"PrivateKey = {self.private_key}",
            f"Address = {self.ip_address}/{WIREGUARD_SUBNET.prefixlen}",
            f"",
            f"[Peer]",
            f"PublicKey = {WIREGUARD_PUBLIC_KEY}",
            f"PresharedKey = {WIREGUARD_PRESHARED_KEY}",
            f"AllowedIPs = {WIREGUARD_SUBNET}",
            f"Endpoint = {WIREGUARD_ENDPOINT}",
            f"PersistentKeepalive = {WIREGUARD_KEEP_ALIVE}",
        ]

        return "\n".join(result)

    def gen_server_side_config(self) -> str:
        result = [
            f"[Peer]",
            f"PublicKey = {self.public_key}",
            f"PresharedKey = {WIREGUARD_PRESHARED_KEY}",
            f"AllowedIPs = {self.ip_address}/32",
        ]

        return "\n".join(result)

    class Settings:
        name = "Connections"


class ConnectionInfoPublic(BaseModel):
    public_key: str
    ip_address: str
