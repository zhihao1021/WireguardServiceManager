from asyncio import get_event_loop, run
from os import getpid

from api import run_api
from database.database import setup
from wireguard_status import status_update_task


async def main():
    await setup()

    loop = get_event_loop()
    auto_update = loop.create_task(status_update_task())

    await run_api()

    auto_update.cancel()


if __name__ == "__main__":
    with open("pid", "w") as pid_file:
        pid_file.write(str(getpid()))
    try:
        run(main=main())
    except KeyboardInterrupt:
        pass
