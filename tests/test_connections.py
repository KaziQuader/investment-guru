import os
from dotenv import load_dotenv
from pymongo import MongoClient
from qdrant_client import QdrantClient
from huggingface_hub import HfApi

load_dotenv()


def test_mongo_connection():
    client = MongoClient(os.getenv("MONGODB_URI"))
    client.admin.command("ping")
    print("MongoDB connection successful")
    client.close()


def test_qdrant_connection():
    client = QdrantClient(
        url=os.getenv("QDRANT_CLOUD_URL"), api_key=os.getenv("QDRANT_APIKEY")
    )
    client.get_collections()
    print("Qdrant connection successful")
    client.close()


def test_huggingface_connection():
    client = HfApi(token=os.getenv("HUGGINGFACE_ACCESS_TOKEN"))
    user = client.whoami()
    print(f"Huggingface connection successful {user['name']}")


if __name__ == "__main__":
    test_mongo_connection()
    test_qdrant_connection()
    test_huggingface_connection()
