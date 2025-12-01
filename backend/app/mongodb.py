from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

    async def connect(self):
        try:
            # Set connection timeout and server selection timeout
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 seconds
                connectTimeoutMS=10000,  # 10 seconds
                socketTimeoutMS=10000,  # 10 seconds
            )
            self.database = self.client.get_database()

            # Verify connection with a ping
            await self.client.admin.command('ping')
            print("Connected to MongoDB successfully")
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            error_msg = f"Failed to connect to MongoDB: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            # Don't raise - allow app to start even if MongoDB is temporarily unavailable
            # Health check will show the issue

    async def close(self):
        try:
            if self.client:
                self.client.close()
                print("Disconnected from MongoDB")
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")

mongodb = MongoDB()
