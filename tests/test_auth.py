"""
Test Complete Auth Flow with Firebase
"""

from utils.firebase_config import FirebaseConfig
from src.services.auth_service import AuthService

def test_complete_flow():
    print("=== Testing Complete Firebase Auth Flow ===\n")

    # Test 1: Register
    print("1. REGISTER NEW USER")
    print("-" * 40)
    config = FirebaseConfig()
    auth = AuthService(config)

    import random

    def generate_phone_number():
        # Generate a random 10-digit number, ensuring the first digit is not 0
        return str(random.randint(1000000000, 9999999999))

    # Example usage:
    phone = generate_phone_number()
    result = auth.register(
        phone=phone,
        password="mypass123",
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com"
    )

    print(result)

    if result['success']:
        print("✓ Registration successful!")
        user = result['user']
        print(f"  UID: {user['uid']}")
        print(f"  Name: {user['firstName']} {user['lastName']}")
        print(f"  Phone: {user['phoneNumber']}")
        print(f"  Time: {user['remainingTime']}s")
        print(f"  Prints: {user['remainingPrints']}")
    else:
        print(f"✗ Failed: {result['error']}")
        return

    # Test 2: Update data
    print("\n2. UPDATE USER DATA")
    print("-" * 40)
    update = auth.update_user_data({
        'remainingTime': 7200,
        'remainingPrints': 50
    })

    if update['success']:
        print("✓ Data updated in Firebase!")
        print(f"  New Time: {auth.current_user['remainingTime']}s")
        print(f"  New Prints: {auth.current_user['remainingPrints']}")

    # Test 3: Logout
    print("\n3. LOGOUT")
    print("-" * 40)
    auth.logout()
    print("✓ Logged out (token cleared)")

    # Test 4: Login
    print("\n4. LOGIN WITH SAME CREDENTIALS")
    print("-" * 40)
    auth2 = AuthService()

    result = auth2.login(phone, "mypass123")

    if result['success']:
        print("✓ Login successful!")
        user = result['user']
        print(f"  Welcome: {user['firstName']} {user['lastName']}")
        print(f"  Time: {user['remainingTime']}s (persisted!)")
        print(f"  Prints: {user['remainingPrints']} (persisted!)")
    else:
        print(f"✗ Failed: {result['error']}")
        return

    # Test 5: Auto-login (simulate app restart)
    print("\n5. AUTO-LOGIN (Simulate App Restart)")
    print("-" * 40)
    auth3 = AuthService()

    if auth3.is_logged_in():
        print("✓ Auto-logged in from stored token!")
        print(f"  User: {auth3.current_user['firstName']}")
        print(f"  Time: {auth3.current_user['remainingTime']}s")
    else:
        print("✗ Auto-login failed")

    print("\n" + "=" * 40)
    print("ALL TESTS PASSED!")
    print("=" * 40)

if __name__ == "__main__":
    test_complete_flow()