from orjson import dumps, loads
from pywgkey import WgKey

from argparse import ArgumentParser
from asyncio import create_task, gather, run as run_sync
from ipaddress import IPv4Address, IPv4Network
from subprocess import PIPE, run
from typing import Any, Callable, Optional

from config import Config


def valid_input(option: str, default: Any, valid_func: Optional[Callable] = None) -> Any:
    while True:
        result = input(f"{option} [{default}]: ") or default
        if valid_func is None:
            return result
        try:
            valid = valid_func(result)
            if type(valid) == bool:
                assert valid == True
            return result
        except:
            print("Invalid input")


def minmax(min: int, max: int):
    def wrap(value) -> bool:
        return min <= int(value) <= max
    return wrap


async def setup_keypair():
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

    default_path = f"/etc/wireguard/{WIREGUARD_INTERFACE}.conf"
    CONF_PATH = input(f"Your conf path [{default_path}]: ") or default_path

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

    with open(CONF_PATH, "w", encoding="utf-8") as conf_file:
        conf_file.write("\n".join(server_side_config))

    print("Restart interface...")
    run(["wg-quick", "down", WIREGUARD_INTERFACE])
    run(["wg-quick", "up", WIREGUARD_INTERFACE])
    print("Finish!")


def setup_config():
    reset_confirm = input(
        "This will clear current config, are you want to coutinue? [y/N] ")
    if not reset_confirm.lower().startswith("y"):
        print("User cancelled.")
        return

    config = Config()
    print("======== API Config ========")
    config.host = valid_input("API Host", config.host, IPv4Address)
    config.port = valid_input("API Port", config.port, minmax(1, 65535))

    wg_config = config.wireguard_config
    print("\n======== Wireguard Config ========")
    config.wireguard_config.subnet = valid_input(
        "Wireguard Subnet", wg_config.subnet, IPv4Network)
    config.wireguard_config.mtu = int(valid_input(
        "Wireguard MTU", wg_config.mtu, minmax(576, 65535)))
    config.wireguard_config.port = int(valid_input(
        "Wireguard Port", wg_config.port, minmax(1, 65535)))
    config.wireguard_config.interface_name = valid_input(
        "Wireguard Interface Name", wg_config.interface_name)

    if input("Do you want forward traffic to internet [y/N] ").lower().startswith("y"):
        ifname = config.wireguard_config.interface_name

        post_up = f"iptables -A FORWARD -i {ifname} -j ACCEPT && iptables -A FORWARD -o {ifname} -j ACCEPT"

        if not input("Do you want enable NAT [Y/n] ").lower().startswith("n"):
            proc = run(["ip", "-br", "-s", "link", "show"], stdout=PIPE)
            interfaces: list[str] = list(map(
                lambda data: data["ifname"],
                filter(
                    lambda data: data["operstate"] == "UP",
                    loads(proc.stdout)
                )
            ))

            choose_ifname = input(
                f"Please input your interface name [{'|'.join(interfaces)}]: ") or interfaces[0]

            post_up += f" && iptables -t nat -A POSTROUTING -o {choose_ifname} -j MASQUERADE"

        config.wireguard_config.post_up = post_up
        config.wireguard_config.post_down = post_up.replace(" -A ", " -D ")

        print("Please remember add `net.ipv4.ip_forward=1` into /etc/sysctl.conf")

    config.wireguard_config.endpoint = valid_input(
        "Wrieguard Endpoint", wg_config.endpoint)
    config.wireguard_config.keep_alive = int(valid_input(
        "Wrieguard Keey Alive", wg_config.keep_alive))
    wg_addition_ip = []
    print("If you want to add additional ips, please type following or keep blank to continue config:")
    while True:
        value = input()
        if value == "":
            break
        try:
            IPv4Address(value)
            wg_addition_ip.append(value)
        except:
            print("Invalid IP subnet address.")
    config.wireguard_config.addition_ips = wg_addition_ip

    mongo_config = config.mongodb_config
    config.mongodb_config.uri = valid_input(
        "MongoDB Connect URI", mongo_config.uri)
    config.mongodb_config.db_name = valid_input(
        "MongoDB DB Name", mongo_config.db_name)

    config.discord_config.redirect_uri = input("Discord Redirect URI: ")
    config.discord_config.client_id = input("Discord Client ID: ")
    config.discord_config.client_secret = input("Discord Client Secret: ")

    valid_config = Config(**config.model_dump())
    print("\nWrite into config.json ...")
    with open("config.json", "wb") as config_file:
        config_file.write(dumps(valid_config.model_dump()))

    print("\nSetting finish, please goto check config.json make sure it is correctly setup.")
    print("\nAfter you checke, please run `python3 setup.py -s` to generate key pairs.")


if __name__ == "__main__":
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c", "--config",
        action="store_true",
        help="Create and setup the config file"
    )
    group.add_argument(
        "-s", "--setup",
        action="store_true",
        help="Generate key pairs and setup wireguard conf"
    )

    args = parser.parse_args()
    if args.config:
        setup_config()
    elif args.setup:
        run_sync(setup_keypair())
    else:
        parser.print_help()
