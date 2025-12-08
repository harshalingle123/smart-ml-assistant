"""Quick script to upload sample dataset"""
import requests
import sys

BASE_URL = "http://localhost:8000"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"

def upload_sample_dataset():
    # 1. Login
    print("[1/3] Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )

    if response.status_code != 200:
        # Try register
        print("[1/3] Registering new user...")
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Test User"
            }
        )

    if response.status_code not in [200, 201]:
        print(f"[ERROR] Authentication failed: {response.status_code}")
        print(response.text)
        return False

    token = response.json().get("access_token")
    print("[OK] Authenticated!")

    # 2. Upload dataset
    print("[2/3] Uploading dataset to Azure...")
    headers = {"Authorization": f"Bearer {token}"}

    with open("sample_dataset.csv", "rb") as f:
        files = {"file": ("sample_dataset.csv", f, "text/csv")}
        response = requests.post(
            f"{BASE_URL}/api/datasets/upload",
            headers=headers,
            files=files
        )

    if response.status_code not in [200, 201]:
        print(f"[ERROR] Upload failed: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    dataset_id = data.get("id")
    azure_url = data.get("azureDatasetUrl")

    print(f"[OK] Dataset uploaded!")
    print(f"     Dataset ID: {dataset_id}")
    print(f"     Azure URL: {azure_url}")
    print(f"     Status: {data.get('status')}")
    print(f"     Rows: {data.get('rowCount')}")
    print(f"     Columns: {data.get('columnCount')}")

    # 3. Show URL
    print(f"\n[3/3] Dataset ready!")
    print(f"\nOpen this URL in your browser:")
    print(f"http://localhost:5173/datasets/{dataset_id}")
    print(f"\nAll components will be visible:")
    print(f"  - Dataset Information")
    print(f"  - Target Column Selector")
    print(f"  - Train Model Button")
    print(f"  - Schema Table (fetched from Azure)")
    print(f"  - Sample Data Table (fetched from Azure)")

    return True

if __name__ == "__main__":
    success = upload_sample_dataset()
    sys.exit(0 if success else 1)
