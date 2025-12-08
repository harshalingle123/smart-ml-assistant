"""
Quick script to check a specific dataset in MongoDB
"""
import asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def check_dataset():
    # Connect to MongoDB Atlas (same as backend)
    mongo_uri = "mongodb+srv://Harshal:Harshal%40123@cluster0.hguakgq.mongodb.net/smartml?appName=Cluster0"
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database()

    dataset_id = "693465b3b05bb749a111f60d"

    print(f"\n{'='*80}")
    print(f"Checking dataset: {dataset_id}")
    print(f"{'='*80}\n")

    # Get the dataset
    dataset = await db.datasets.find_one({"_id": ObjectId(dataset_id)})

    if not dataset:
        print(f"[X] Dataset not found!")
        return

    print(f"[OK] Dataset found:")
    print(f"  Name: {dataset.get('name')}")
    print(f"  File Name: {dataset.get('file_name')}")
    print(f"  Status: {dataset.get('status')}")
    print(f"  Row Count: {dataset.get('row_count')}")
    print(f"  Column Count: {dataset.get('column_count')}")
    print(f"  Source: {dataset.get('source')}")
    print(f"  Azure URL: {dataset.get('azure_dataset_url')}")
    print(f"  Target Column: {dataset.get('target_column')}")

    # Check if it has schema/sample_data in MongoDB (should be None)
    has_schema = 'schema' in dataset and dataset.get('schema') is not None
    has_sample_data = 'sample_data' in dataset and dataset.get('sample_data') is not None

    print(f"\n  Has schema in MongoDB: {has_schema}")
    if has_schema:
        print(f"    [WARNING] Schema found in MongoDB ({len(dataset.get('schema'))} columns)")

    print(f"  Has sample_data in MongoDB: {has_sample_data}")
    if has_sample_data:
        print(f"    [WARNING] Sample data found in MongoDB ({len(dataset.get('sample_data'))} rows)")

    # Check if Azure URL exists
    if not dataset.get('azure_dataset_url'):
        print(f"\n  [ERROR] No Azure URL found! Data cannot be loaded.")
    else:
        print(f"\n  [OK] Azure URL exists: {dataset.get('azure_dataset_url')}")

    # If schema/sample_data exist, offer to remove them
    if has_schema or has_sample_data:
        print(f"\n{'='*80}")
        print(f"CLEANUP NEEDED!")
        print(f"{'='*80}")
        print(f"This dataset has schema/sample_data stored in MongoDB.")
        print(f"They should be removed so data is fetched from Azure instead.")

        response = input(f"\nDo you want to remove schema/sample_data from MongoDB? (yes/no): ")
        if response.lower() == 'yes':
            update_result = await db.datasets.update_one(
                {"_id": ObjectId(dataset_id)},
                {"$unset": {"schema": "", "sample_data": ""}}
            )
            print(f"\n[OK] Removed schema/sample_data from MongoDB")
            print(f"   Modified count: {update_result.modified_count}")
            print(f"\n   The GET endpoint will now fetch data from Azure!")
    else:
        print(f"\n[OK] GOOD! No schema/sample_data in MongoDB - data will be fetched from Azure")

    print(f"\n{'='*80}\n")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_dataset())
