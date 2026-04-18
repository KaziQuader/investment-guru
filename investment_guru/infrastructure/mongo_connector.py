"""
MongoDB connection management using Motor (async) + Beanie ODM.

Usage
-----
Call `MongoDBConnector.connect()` once at startup (e.g. in your ZenML step
or pipeline entrypoint) before any document operations.

    from investment_guru.infrastructure.mongo_connector import MongoDBConnector

    async def main():
        await MongoDBConnector.connect()
        # ... use Beanie documents freely ...
        await MongoDBConnector.disconnect()
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from investment_guru.domain.documents.stocks import StockDocument
from investment_guru.domain.documents.news import NewsDocument
from investment_guru.domain.documents.filing import FilingDocument

load_dotenv()

logger = logging.getLogger(__name__)

# All Beanie document models registered with the database
DOCUMENT_MODELS = [StockDocument, NewsDocument, FilingDocument]

_client: AsyncIOMotorClient | None = None


class MongoDBConnector:
    """Manages the lifecycle of the MongoDB async connection."""

    @staticmethod
    async def connect(database_name: str = "investment_guru") -> None:
        """
        Open connection to MongoDB Atlas and initialise Beanie.

        Parameters
        ----------
        database_name : str
            The database to use inside the Atlas cluster.
            Defaults to 'investment_guru'.
        """
        global _client

        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise EnvironmentError(
                "MONGODB_URI is not set. "
                "Add it to your .env file or environment variables."
            )

        # Workaround for modern PyMongo/Motor + Beanie compatibility bug
        # Beanie attempts to execute client.append_metadata which doesn't exist
        AsyncIOMotorClient.append_metadata = lambda self, *args, **kwargs: None
        _client = AsyncIOMotorClient(mongodb_uri)
        await init_beanie(
            database=_client[database_name],
            document_models=DOCUMENT_MODELS,
        )
        logger.info("Connected to MongoDB database '%s'", database_name)

    @staticmethod
    async def disconnect() -> None:
        """Close the MongoDB connection."""
        global _client
        if _client is not None:
            _client.close()
            _client = None
            logger.info("Disconnected from MongoDB")
