from asyncio import get_event_loop, run

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
    try:
        run(main=main())
    except KeyboardInterrupt:
        pass
