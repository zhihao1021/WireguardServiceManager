from time import time
from fastapi import WebSocket
from orjson import dumps

from asyncio import (
    CancelledError,
    create_task,
    gather,
    sleep as asleep
)
from subprocess import run, PIPE

from config import WIREGUARD_INTERFACE

STATUS: dict[str, int] = {}


class AutoPublisher():
    websockets: list[WebSocket]

    def __init__(self):
        self.websockets = []

    async def add_subscriber(self, ws: WebSocket):
        await ws.send_bytes(dumps(STATUS))
        self.websockets.append(ws)

    async def send_all(self):
        message = dumps(STATUS)
        await gather(*list(map(
            lambda ws: create_task(ws.send_bytes(message)),
            self.websockets
        )), return_exceptions=True)

    def remove_subscriber(self, ws: WebSocket):
        if ws in self.websockets:
            self.websockets.remove(ws)


PUBLISHER = AutoPublisher()


async def status_update_task():
    try:
        while True:
            proc = run(
                args=["wg", "show", WIREGUARD_INTERFACE, "latest-handshakes"],
                stdout=PIPE
            )
            results = proc.stdout.decode().strip().split("\n")

            for result in results:
                public_key, time = result.split("\t")
                STATUS[public_key] = int(time)
            # STATUS["B9ileVkCXT4NeAu/ZBj7LCFYfo4N2xDAdetrOrRpNws="] = int(
            #     time())

            await PUBLISHER.send_all()

            for _ in range(10):
                await asleep(1)
    except CancelledError:
        return
