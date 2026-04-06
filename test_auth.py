"""Test authentication endpoints."""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup():
    """Test the signup endpoint."""
    print("\n=== Test Signup ===")
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "email": "testuser2@example.com",
            "password": "TestPass123",
            "role": "client"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.ok else None

def test_login(email="testuser2@example.com", password="TestPass123"):
    """Test the login endpoint."""
    print("\n=== Test Login ===")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.ok else None

def test_me(access_token):
    """Test the /auth/me endpoint."""
    print("\n=== Test /auth/me ===")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.ok else None

def test_commitment_still_works():
    """Test that existing commitment endpoint still works."""
    print("\n=== Test Existing Commitment Endpoint ===")
    response = requests.get(f"{BASE_URL}/commitments/1")
    print(f"Status: {response.status_code}")
    if response.ok:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Response: {response.text}")

def main():
    print("=" * 60)
    print("AUTHENTICATION ENDPOINT TESTS")
    print("=" * 60)
    
    # Test signup
    signup_result = test_signup()
    
    # Test login
    login_result = test_login()
    
    if login_result:
        # Test /auth/me with the token
        test_me(login_result["access_token"])
    
    # Test that existing endpoints still work
    test_commitment_still_works()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
