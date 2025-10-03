"""
Test Complete Auth Flow with Firebase
"""

import sys
from pathlib import Path

# Add src to path for importing
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

# Initialize logging using the centralized system
from utils.logger import SionyxLogger, get_logger
import logging

# Setup logging for tests
SionyxLogger.setup(log_level=logging.INFO, log_to_file=False)
logger = get_logger(__name__)

from utils.firebase_config import FirebaseConfig
from services.auth_service import AuthService

def generate_phone_number():
    """Generate random 10-digit phone number"""
    import random
    return str(random.randint(1000000000, 9999999999))


def test_complete_flow():
    logger.info("=== Testing Complete Firebase Auth Flow ===")

    # Test 1: Register
    logger.info("1. REGISTER NEW USER")
    logger.info("-" * 40)
    config = FirebaseConfig()
    auth = AuthService(config)


    # Generate phone once for entire test
    test_phone = generate_phone_number()
    test_password = "mypass123"

    logger.info(f"Test Phone: {test_phone}")
    logger.info(f"Test Password: {test_password}")

    # Test 1: Register
    logger.info("1. REGISTER NEW USER")
    logger.info("-" * 40)
    auth = AuthService()

    result = auth.register(
        phone=test_phone,
        password=test_password,
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com"
    )

    if result['success']:
        logger.info("✓ Registration successful!")
        user = result['user']
        logger.info(f"  UID: {user['uid']}")
        logger.info(f"  Name: {user['firstName']} {user['lastName']}")
        logger.info(f"  Phone: {user['phoneNumber']}")
        logger.info(f"  Is Admin: {user.get('isAdmin', False)}")
        logger.info(f"  Time: {user['remainingTime']}s")
        logger.info(f"  Prints: {user['remainingPrints']}")
    else:
        logger.error(f"✗ Failed: {result['error']}")
        return

    # Test 2: Update data
    logger.info("2. UPDATE USER DATA")
    logger.info("-" * 40)
    update = auth.update_user_data({
        'remainingTime': 7200,
        'remainingPrints': 50
    })

    if update['success']:
        logger.info("✓ Data updated in Firebase!")
        logger.info(f"  New Time: {auth.current_user['remainingTime']}s")
        logger.info(f"  New Prints: {auth.current_user['remainingPrints']}")

    # Test 3: Logout
    logger.info("3. LOGOUT")
    logger.info("-" * 40)
    auth.logout()
    logger.info("✓ Logged out (token cleared)")

    # Test 4: Login with SAME phone
    logger.info("4. LOGIN WITH SAME CREDENTIALS")
    logger.info("-" * 40)
    auth2 = AuthService()

    result = auth2.login(test_phone, test_password)

    if result['success']:
        logger.info("✓ Login successful!")
        user = result['user']
        logger.info(f"  Welcome: {user['firstName']} {user['lastName']}")
        logger.info(f"  Time: {user['remainingTime']}s (persisted!)")
        logger.info(f"  Prints: {user['remainingPrints']} (persisted!)")
        logger.info(f"  Is Admin: {user.get('isAdmin', False)}")
    else:
        logger.error(f"✗ Failed: {result['error']}")
        return

    # Test 5: Auto-login (simulate app restart)
    logger.info("5. AUTO-LOGIN (Simulate App Restart)")
    logger.info("-" * 40)
    auth3 = AuthService()

    if auth3.is_logged_in():
        logger.info("✓ Auto-logged in from stored token!")
        logger.info(f"  User: {auth3.current_user['firstName']}")
        logger.info(f"  Time: {auth3.current_user['remainingTime']}s")
    else:
        logger.error("✗ Auto-login failed")

    logger.info("=" * 40)
    logger.info("ALL TESTS PASSED!")
    logger.info("=" * 40)


def create_admin_user():
    """Helper to create an admin user for testing"""
    logger.info("=== Creating Admin User ===")

    admin_phone = input("Admin Phone (e.g., 0501234567): ")
    admin_password = input("Admin Password: ")

    auth = AuthService()

    # Register admin
    result = auth.register(
        phone=admin_phone,
        password=admin_password,
        first_name="Admin",
        last_name="User",
        email="admin@sionyx.app"
    )

    if not result['success']:
        logger.error(f"✗ Failed to create admin: {result['error']}")
        return

    uid = result['user']['uid']
    logger.info(f"✓ Admin user created: {uid}")

    # Update to make admin
    logger.info("Setting isAdmin flag...")
    update_result = auth.firebase.db_update(f'users/{uid}', {
        'isAdmin': True
    })

    if update_result['success']:
        logger.info("✓ User is now admin!")
        logger.info("Admin credentials:")
        logger.info(f"  Phone: {admin_phone}")
        logger.info(f"  Password: {admin_password}")
        logger.info(f"  UID: {uid}")
    else:
        logger.error(f"✗ Failed to set admin flag: {update_result.get('error')}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--create-admin':
        create_admin_user()
    else:
        test_complete_flow()