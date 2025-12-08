"""
List all datasets in MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def list_datasets():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["smart_ml"]

    print(f"\n{'='*80}")
    print(f"All Datasets in MongoDB")
    print(f"{'='*80}\n")

    # Get all datasets
    cursor = db.datasets.find({}).sort("_id", -1).limit(10)
    datasets = await cursor.to_list(length=10)

    if not datasets:
        print(f"[X] No datasets found in the database!")
        client.close()
        return

    print(f"[OK] Found {len(datasets)} datasets (showing most recent 10):\n")

    for i, dataset in enumerate(datasets, 1):
        print(f"{i}. ID: {dataset.get('_id')}")
        print(f"   Name: {dataset.get('name')}")
        print(f"   Status: {dataset.get('status')}")
        print(f"   Source: {dataset.get('source', 'upload')}")
        print(f"   Azure URL: {'YES' if dataset.get('azure_dataset_url') else 'NO'}")
        print(f"   Has schema: {'YES' if dataset.get('schema') else 'NO'}")
        print(f"   Has sample_data: {'YES' if dataset.get('sample_data') else 'NO'}")
        print()

    client.close()

if __name__ == "__main__":
    asyncio.run(list_datasets())
