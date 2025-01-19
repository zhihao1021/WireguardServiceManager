from bcrypt import gensalt
from orjson import dumps, loads, OPT_INDENT_2
from pydantic import BaseModel
from pywgkey import WgKey, WgPsk

from ipaddress import IPv4Network
from logging import getLogger
from os import urandom
from typing import Optional

psk = WgPsk()
key_pair = WgKey()


class WireguardConfig(BaseModel):
    subnet: str = "192.168.250.0/24"
    mtu: int = 1500
    port: int = 51820
    public_key: str = key_pair.pubkey
    private_key: str = key_pair.privkey
    preshared_key: str = psk.key
    post_up: Optional[str] = None
    post_down: Optional[str] = None
    interface_name: str = "wg0"
    endpoint: str = "example.com:51820"
    keey_alive: int = 30
    addition_ips: list[str] = []


class MongoDBConfig(BaseModel):
    uri: str = "mongodb+srv://username:password@example.com/wsm"
    db_name: str = "wsm"
    use_tls: bool = False
    tls_cafile: Optional[str] = None


class DiscordConfig(BaseModel):
    redirect_uri: str = ""
    client_id: str = ""
    client_secret: str = ""


class Config(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    jwt_key: str = gensalt().decode() + urandom(16).hex()
    join_key: str = gensalt().decode() + urandom(16).hex()
    wireguard_config: WireguardConfig = WireguardConfig()
    mongodb_config: MongoDBConfig = MongoDBConfig()
    discord_config: DiscordConfig = DiscordConfig()


if __name__ == "config":
    logger = getLogger("config")
    try:
        with open("config.json", "rb") as config_file:
            config = Config(**loads(config_file.read()))

        HOST = config.host
        PORT = config.port
        JWT_KEY = config.jwt_key
        JOIN_KEY = config.join_key

        WIREGUARD_SUBNET = IPv4Network(config.wireguard_config.subnet)
        WIREGUARD_MTU = config.wireguard_config.mtu
        WIREGUARD_PORT = config.wireguard_config.port
        WIREGUARD_PRIVATE_KEY = config.wireguard_config.private_key
        WIREGUARD_PUBLIC_KEY = config.wireguard_config.public_key
        WIREGUARD_PRESHARED_KEY = config.wireguard_config.preshared_key
        WIREGUARD_POST_UP = config.wireguard_config.post_up
        WIREGUARD_POST_DOWN = config.wireguard_config.post_down
        WIREGUARD_INTERFACE = config.wireguard_config.interface_name
        WIREGUARD_ENDPOINT = config.wireguard_config.endpoint
        WIREGUARD_KEEP_ALIVE = config.wireguard_config.keey_alive
        WIREGUARD_ADDITION_IPS = config.wireguard_config.addition_ips

        MONGODB_URI = config.mongodb_config.uri
        MONGODB_DB = config.mongodb_config.db_name
        MONGODB_TLS = config.mongodb_config.use_tls
        MONGODB_CAFILE = config.mongodb_config.tls_cafile

        DISCORD_REDIRECT_URI = config.discord_config.redirect_uri
        DISCORD_CLIENT_ID = config.discord_config.client_id
        DISCORD_CLIENT_SECRET = config.discord_config.client_secret
    except:
        logger.error(
            "No config file found, auto generate a new config file...")
        with open("config.json", "wb") as config_file:
            config_file.write(dumps(
                Config().model_dump(),
                option=OPT_INDENT_2
            ))
        logger.error("Please go to modify the config.json.")
        exit(0)

    with open("config.json", "wb") as config_file:
        config_file.write(dumps(config.model_dump(), option=OPT_INDENT_2))
