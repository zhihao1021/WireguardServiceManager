from pywgkey import WgKey

from asyncio import create_task, gather, run
from ipaddress import IPv4Address

from config import (
    WIREGUARD_SUBNET,
    WIREGUARD_PRIVATE_KEY,
    WIREGUARD_PORT,
    WIREGUARD_MTU,
    WIREGUARD_POST_UP,
    WIREGUARD_POST_DOWN,
    WIREGUARD_INTERFACE
)
from database.database import setup
from scheams.connection_info import ConnectionInfo
from scheams.user import UserData


async def main():
    await setup()

    await ConnectionInfo.delete_all()

    ips = list(WIREGUARD_SUBNET.hosts())[1:]

    def gen_connection(ip: IPv4Address) -> ConnectionInfo:
        key = WgKey()
        return ConnectionInfo(
            private_key=key.privkey,
            public_key=key.pubkey,
            ip_address=str(ip),
        )

    connections = list(map(gen_connection, ips))

    await ConnectionInfo.insert_many(connections)
    connections = await ConnectionInfo.find_all().to_list()

    users = await UserData.find_all().to_list()
    if len(users) > len(connections):
        raise RuntimeError("IP Not Enough")

    async def task(user: UserData, conn: ConnectionInfo):
        conn.discord_user_id = user.discord_id
        user.connection = conn

        await conn.save()
        await user.save()

    await gather(*list(map(
        lambda pair: create_task(task(*pair)),
        zip(users, connections)
    )))

    server_ip = list(WIREGUARD_SUBNET.hosts())[0]
    server_side_config = [
        f"[Interface]",
        f"Address = {server_ip}/{WIREGUARD_SUBNET.prefixlen}",
        f"PrivateKey = {WIREGUARD_PRIVATE_KEY}",
        f"ListenPort = {WIREGUARD_PORT}",
        f"MTU = {WIREGUARD_MTU}",
    ]
    if WIREGUARD_POST_UP and WIREGUARD_POST_DOWN:
        server_side_config.append(f"PostUp = {WIREGUARD_POST_UP}")
        server_side_config.append(f"PostDown = {WIREGUARD_POST_DOWN}")

    for conn in connections:
        server_side_config.append("")
        server_side_config.append(conn.gen_server_side_config())

    with open(f"/etc/wireguard/{WIREGUARD_INTERFACE}.conf", "w", encoding="utf-8") as conf_file:
        conf_file.write("\n".join(server_side_config))


if __name__ == "__main__":
    run(main=main())
