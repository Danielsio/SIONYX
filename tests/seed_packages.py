"""
Seed dummy packages to Firebase Realtime Database
Run this once to populate test data
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from services.firebase_client import FirebaseClient
from datetime import datetime


def seed_packages():
    """Create dummy packages in Firebase"""

    print("🌱 Seeding packages to Firebase...\n")

    client = FirebaseClient()

    # You need to be authenticated to write to database
    # Use your admin credentials
    print("Please sign in with admin account:")
    email = input("Email (phone@sionyx.app): ")
    password = input("Password: ")

    result = client.sign_in(email, password)

    if not result.get('success'):
        print(f"❌ Authentication failed: {result.get('error')}")
        return

    print(f"✅ Authenticated as: {result['uid']}\n")

    # Define packages
    packages = [
        {
            "name": "Quick Session",
            "description": "Perfect for checking emails and quick tasks",
            "minutes": 30,
            "prints": 5,
            "price": 25,
            "discountPercent": 0,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        {
            "name": "Standard Hour",
            "description": "Great for general browsing and work",
            "minutes": 60,
            "prints": 10,
            "price": 40,
            "discountPercent": 15,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        {
            "name": "Power User",
            "description": "Extended session with extra print credits",
            "minutes": 180,
            "prints": 30,
            "price": 100,
            "discountPercent": 20,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        {
            "name": "Student Special",
            "description": "Affordable package for students",
            "minutes": 120,
            "prints": 20,
            "price": 60,
            "discountPercent": 25,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        {
            "name": "All-Day Pass",
            "description": "Full day access with unlimited prints",
            "minutes": 480,
            "prints": 100,
            "price": 150,
            "discountPercent": 10,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
    ]

    # Upload to Firebase
    for i, package in enumerate(packages, 1):
        print(f"📦 Creating package {i}/{len(packages)}: {package['name']}")

        # Push to Firebase (auto-generates ID)
        result = client.firebase.post(
            url=f"{client.database_url}/packages.json",
            params={'auth': client.id_token},
            json=package
        )

        if result.status_code == 200:
            pkg_id = result.json()['name']
            print(f"   ✅ Created with ID: {pkg_id}")
        else:
            print(f"   ❌ Failed: {result.text}")

    print("\n🎉 Package seeding complete!")
    print("\nVerify at: https://console.firebase.google.com/")
    print("Go to Realtime Database → packages")


if __name__ == "__main__":
    try:
        seed_packages()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")