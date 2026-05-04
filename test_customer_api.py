#!/usr/bin/env python3
"""
Test script for Customer API endpoint.
Run this to diagnose 400 Bad Request errors on POST /api/v1/customers
"""

import httpx
import sys

# Configuration - Update these values
BASE_URL = "http://localhost:8000"  # Your backend URL
EMAIL = "admin@crater.local"
PASSWORD = "Admin123!"

def test_customer_creation():
    """Test creating a customer with various payloads"""
    
    print("=" * 60)
    print("Customer API Test Script")
    print("=" * 60)
    
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # Step 1: Login to get token
        print("\n1. Logging in...")
        try:
            response = client.post(
                "/api/v1/auth/login",
                data={"username": EMAIL, "password": PASSWORD}
            )
            if response.status_code != 200:
                print(f"   ✗ Login failed: {response.status_code}")
                print(f"   Response: {response.json()}")
                print("\n   Make sure you have a user created.")
                print("   Run: python create_user_and_signin.py create --email admin@crater.local --password Admin123! --name 'Admin User'")
                return False
            
            token = response.json()["access_token"]
            print(f"   ✓ Login successful")
        except Exception as e:
            print(f"   ✗ Login error: {e}")
            return False
        
        # Step 2: Get company ID from token or use default
        import jwt
        from jwt.exceptions import PyJWTError
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            company_id = decoded.get("company_id", 1)
            print(f"   ✓ Using company ID: {company_id}")
        except PyJWTError:
            company_id = 1
            print(f"   ! Could not decode token, using default company ID: {company_id}")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "company": str(company_id)
        }
        
        # Step 3: Test various payloads
        test_cases = [
            {
                "name": "Minimal valid payload",
                "data": {"name": "Test Customer"},
                "should_succeed": True
            },
            {
                "name": "Full payload with email",
                "data": {
                    "name": "Acme Corporation",
                    "email": "contact@acme.com",
                    "phone": "+1-555-123-4567",
                    "company_name": "Acme Corp",
                    "contact_name": "John Doe"
                },
                "should_succeed": True
            },
            {
                "name": "Payload with billing address",
                "data": {
                    "name": "Test Corp",
                    "email": "test@example.com",
                    "billing": {
                        "address_street_1": "123 Main St",
                        "city": "New York",
                        "state": "NY",
                        "zip": "10001",
                        "country_id": 231
                    }
                },
                "should_succeed": True
            },
            {
                "name": "Empty name (should fail)",
                "data": {"name": ""},
                "should_succeed": False
            },
            {
                "name": "Missing name (should fail)",
                "data": {"email": "test@example.com"},
                "should_succeed": False
            },
            {
                "name": "Invalid email format (should fail)",
                "data": {"name": "Test", "email": "not-an-email"},
                "should_succeed": False
            },
            {
                "name": "Empty string email (should fail)",
                "data": {"name": "Test", "email": ""},
                "should_succeed": False
            }
        ]
        
        print("\n2. Testing customer creation:")
        print("-" * 60)
        
        all_passed = True
        for i, test in enumerate(test_cases, 1):
            print(f"\n   Test {i}: {test['name']}")
            try:
                response = client.post(
                    "/api/v1/customers",
                    json=test["data"],
                    headers=headers
                )
                
                success = response.status_code == 201
                expected = test["should_succeed"]
                
                if success == expected:
                    status = "✓ PASS"
                else:
                    status = "✗ FAIL"
                    all_passed = False
                
                print(f"      Status: {response.status_code}")
                print(f"      Result: {status}")
                
                if response.status_code != 201:
                    try:
                        error_detail = response.json()
                        print(f"      Error: {error_detail}")
                    except:
                        print(f"      Error: {response.text[:200]}")
                        
            except Exception as e:
                print(f"      ✗ Exception: {e}")
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed. Check the errors above.")
        print("=" * 60)
        
        return all_passed

if __name__ == "__main__":
    success = test_customer_creation()
    sys.exit(0 if success else 1)
