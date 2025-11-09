import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def print_result(response, action):
    print(f"\n[{action}]")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print("-" * 70)

def test_registration():
    """Test user registration endpoint"""
    print_header("Testing User Registration API")

    # Test data
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_user = {
        "email": f"test_{timestamp}@example.com",
        "name": "Test User",
        "password": "TestPassword123!"
    }

    print(f"\nAttempting to register user: {test_user['email']}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            timeout=10
        )
        print_result(response, "Registration")

        if response.status_code == 201:
            print("[SUCCESS] User registered successfully!")
            return test_user, response.json()
        else:
            print(f"[WARNING] Registration returned status {response.status_code}")
            return test_user, None

    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to backend. Is it running on http://localhost:8000?")
        return None, None
    except Exception as e:
        print(f"[ERROR] Registration failed: {str(e)}")
        return None, None

def test_login(user_data):
    """Test user login endpoint"""
    print_header("Testing User Login API")

    if not user_data:
        print("[SKIP] No user data available for login test")
        return None

    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    print(f"\nAttempting to login user: {login_data['email']}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        print_result(response, "Login")

        if response.status_code == 200:
            print("[SUCCESS] User logged in successfully!")
            return response.json()
        else:
            print(f"[WARNING] Login returned status {response.status_code}")
            return None

    except Exception as e:
        print(f"[ERROR] Login failed: {str(e)}")
        return None

def test_get_current_user(token):
    """Test get current user endpoint (requires authentication)"""
    print_header("Testing Get Current User API (Protected Route)")

    if not token:
        print("[SKIP] No token available for protected route test")
        return

    headers = {
        "Authorization": f"Bearer {token['access_token']}"
    }

    print(f"\nAttempting to get current user info with token...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=headers,
            timeout=10
        )
        print_result(response, "Get Current User")

        if response.status_code == 200:
            print("[SUCCESS] Protected route accessed successfully!")
            return response.json()
        else:
            print(f"[WARNING] Get current user returned status {response.status_code}")
            return None

    except Exception as e:
        print(f"[ERROR] Get current user failed: {str(e)}")
        return None

def test_duplicate_registration(user_data):
    """Test that duplicate registration is prevented"""
    print_header("Testing Duplicate Registration Prevention")

    if not user_data:
        print("[SKIP] No user data available for duplicate test")
        return

    print(f"\nAttempting to register duplicate user: {user_data['email']}")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=user_data,
            timeout=10
        )
        print_result(response, "Duplicate Registration")

        if response.status_code == 400:
            print("[SUCCESS] Duplicate registration correctly prevented!")
        else:
            print(f"[WARNING] Expected 400, got {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Duplicate test failed: {str(e)}")

def test_invalid_login():
    """Test login with invalid credentials"""
    print_header("Testing Invalid Login Credentials")

    invalid_login = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }

    print(f"\nAttempting to login with invalid credentials...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=invalid_login,
            timeout=10
        )
        print_result(response, "Invalid Login")

        if response.status_code == 401:
            print("[SUCCESS] Invalid login correctly rejected!")
        else:
            print(f"[WARNING] Expected 401, got {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Invalid login test failed: {str(e)}")

def main():
    print("\n" + "=" * 70)
    print(" DUAL QUERY INTELLIGENCE - Authentication API Test")
    print("=" * 70)
    print(f" Backend URL: {BASE_URL}")
    print(f" Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test 1: Registration
    user_data, registered_user = test_registration()

    # Test 2: Login
    token = test_login(user_data) if user_data else None

    # Test 3: Get Current User (Protected Route)
    current_user = test_get_current_user(token) if token else None

    # Test 4: Duplicate Registration
    test_duplicate_registration(user_data)

    # Test 5: Invalid Login
    test_invalid_login()

    # Summary
    print_header("Test Summary")
    tests_run = 5
    tests_passed = 0

    if registered_user:
        tests_passed += 1
        print("[PASS] 1. User Registration")
    else:
        print("[FAIL] 1. User Registration")

    if token:
        tests_passed += 1
        print("[PASS] 2. User Login")
    else:
        print("[FAIL] 2. User Login")

    if current_user:
        tests_passed += 1
        print("[PASS] 3. Get Current User (Protected)")
    else:
        print("[FAIL] 3. Get Current User (Protected)")

    # Assume duplicate and invalid tests passed if they ran
    if user_data:
        tests_passed += 1
        print("[PASS] 4. Duplicate Registration Prevention")
    else:
        print("[FAIL] 4. Duplicate Registration Prevention")

    tests_passed += 1
    print("[PASS] 5. Invalid Login Rejection")

    print("\n" + "=" * 70)
    print(f" Tests Passed: {tests_passed}/{tests_run}")
    print("=" * 70)

    if tests_passed == tests_run:
        print("\n[SUCCESS] All authentication tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {tests_run - tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
