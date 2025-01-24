from fastapi import WebSocket
from orjson import dumps

from asyncio import (
    CancelledError,
    create_task,
    gather,
    get_event_loop,
    sleep as asleep
)
from subprocess import run, PIPE, DEVNULL

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
        results = await gather(*list(map(
            lambda ws: create_task(ws.send_bytes(message)),
            self.websockets
        )), return_exceptions=True)

        failed_ws = list(filter(
            lambda pair: results[pair[0]] is not None,
            enumerate(self.websockets)
        ))
        await gather(*list(map(
            lambda pair: create_task(pair[1].close()),
            failed_ws
        )), return_exceptions=None)

        for _, ws in failed_ws:
            self.remove_subscriber(ws)

    def remove_subscriber(self, ws: WebSocket):
        if ws in self.websockets:
            self.websockets.remove(ws)


PUBLISHER = AutoPublisher()


async def status_update_task():
    loop = get_event_loop()
    while True:
        try:
            proc = await loop.run_in_executor(None, lambda: run(
                args=["wg", "show", WIREGUARD_INTERFACE, "latest-handshakes"],
                stdout=PIPE,
                stderr=DEVNULL
            ))
            results = proc.stdout.decode().strip().split("\n")

            if results and len(results[0]) > 0:
                for result in results:
                    public_key, time = result.split("\t")
                    STATUS[public_key] = int(time)

                await PUBLISHER.send_all()
        except CancelledError:
            return
        except:
            pass

        await asleep(15)
