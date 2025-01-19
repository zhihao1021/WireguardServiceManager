from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import (
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_TLS,
    MONGODB_CAFILE
)
from scheams.connection_info import ConnectionInfo
from scheams.user import UserData

client = AsyncIOMotorClient(
    MONGODB_URI,
    tls=MONGODB_TLS,
    tlsCAFile=MONGODB_CAFILE
)

DB = client[MONGODB_DB]


async def setup():
    await init_beanie(
        database=DB,
        document_models=[
            ConnectionInfo,
            UserData
        ]
    )
