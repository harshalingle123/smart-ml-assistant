from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.database = self.client.get_database()
        print("Connected to MongoDB")

    async def close(self):
        self.client.close()
        print("Disconnected from MongoDB")

mongodb = MongoDB()
