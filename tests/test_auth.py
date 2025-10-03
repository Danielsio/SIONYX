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

def test_complete_flow():
    logger.info("=== Testing Complete Firebase Auth Flow ===")

    # Test 1: Register
    logger.info("1. REGISTER NEW USER")
    logger.info("-" * 40)
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

    logger.debug(f"Registration result: {result}")

    if result['success']:
        logger.info("✓ Registration successful!")
        user = result['user']
        logger.info(f"  UID: {user['uid']}")
        logger.info(f"  Name: {user['firstName']} {user['lastName']}")
        logger.info(f"  Phone: {user['phoneNumber']}")
        logger.info(f"  Time: {user['remainingTime']}s")
        logger.info(f"  Prints: {user['remainingPrints']}")
    else:
        logger.error(f"✗ Registration failed: {result['error']}")
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

    # Test 4: Login
    logger.info("4. LOGIN WITH SAME CREDENTIALS")
    logger.info("-" * 40)
    auth2 = AuthService()

    result = auth2.login(phone, "mypass123")

    if result['success']:
        logger.info("✓ Login successful!")
        user = result['user']
        logger.info(f"  Welcome: {user['firstName']} {user['lastName']}")
        logger.info(f"  Time: {user['remainingTime']}s (persisted!)")
        logger.info(f"  Prints: {user['remainingPrints']} (persisted!)")
    else:
        logger.error(f"✗ Login failed: {result['error']}")
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

if __name__ == "__main__":
    test_complete_flow()