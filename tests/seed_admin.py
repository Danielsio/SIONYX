"""
Seed Admin Users for Admin Dashboard

This script creates admin users in Firebase for accessing the admin dashboard.

Usage:
    python tests/seed_admin.py

Environment variables required:
    - FIREBASE_API_KEY
    - FIREBASE_DATABASE_URL
    - FIREBASE_PROJECT_ID
    - ORG_ID
"""

import sys
import os
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from services.firebase_client import FirebaseClient
from datetime import datetime
import getpass


def phone_to_email(phone: str) -> str:
    """Convert phone number to email format for Firebase"""
    clean_phone = ''.join(filter(str.isdigit, phone))
    return f"{clean_phone}@sionyx.app"


def create_admin_user(phone: str, password: str, display_name: str, org_id: str):
    """
    Create an admin user
    
    Args:
        phone: Admin phone number
        password: Admin password (min 6 characters)
        display_name: Admin display name
        org_id: Organization ID the admin belongs to
    """
    firebase = FirebaseClient()
    
    # Convert phone to email format (same as desktop app)
    email = phone_to_email(phone)
    
    print(f"\n🔧 Creating admin user: {phone}")
    print(f"   Email format: {email}")
    print(f"   Organization: {org_id}")
    
    # 1. Create Firebase Auth user
    print("\n📝 Step 1: Creating Firebase Auth user...")
    result = firebase.sign_up(email, password)
    
    if not result.get('success'):
        print(f"❌ Failed to create auth user: {result.get('error')}")
        return False
    
    admin_id = result['uid']
    print(f"✅ Auth user created with ID: {admin_id}")
    
    # 2. Create admin user in organization (stored in users/ with isAdmin flag)
    print(f"\n📝 Step 2: Creating admin user in organizations/{org_id}/users/{admin_id}...")
    
    admin_data = {
        'phone': phone,
        'firstName': display_name.split()[0] if ' ' in display_name else display_name,
        'lastName': ' '.join(display_name.split()[1:]) if ' ' in display_name else '',
        'phoneNumber': phone,
        'email': '',
        'displayName': display_name,
        'isAdmin': True,  # This is what makes them an admin
        'isActive': True,
        'remainingTime': 0,
        'remainingPrints': 0,
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat(),
        'lastLogin': None
    }
    
    # Store admin in users collection with isAdmin=True
    admin_path = f'organizations/{org_id}/users/{admin_id}'
    
    # Temporarily override _get_org_path to return raw path
    original_method = firebase._get_org_path
    firebase._get_org_path = lambda path: path
    
    admin_result = firebase.db_set(admin_path, admin_data)
    
    # Restore original method
    firebase._get_org_path = original_method
    
    if not admin_result.get('success'):
        print(f"❌ Failed to create admin document: {admin_result.get('error')}")
        return False
    
    print(f"✅ Admin user created with isAdmin=True")
    
    print(f"\n✨ Admin user created successfully!")
    print(f"\n📋 Login Details for Admin Dashboard:")
    print(f"   Organization ID: {org_id}")
    print(f"   Phone Number: {phone}")
    print(f"   Password: {password}")
    print(f"\n🌐 Login at the admin dashboard:")
    print(f"   1. Enter Organization ID: {org_id}")
    print(f"   2. Enter Phone Number: {phone}")
    print(f"   3. Enter Password")
    print(f"\n✅ User has isAdmin=True flag and can access admin dashboard")
    
    return True


def main():
    """Main function to create admin users"""
    
    print("=" * 60)
    print("SIONYX Admin User Seeder")
    print("=" * 60)
    
    # Get organization ID from environment
    org_id = os.getenv('ORG_ID')
    
    if not org_id:
        print("\n❌ Error: ORG_ID not found in environment variables")
        print("Please set ORG_ID in your .env file")
        return
    
    print(f"\n🏢 Organization: {org_id}")
    
    # Prompt for admin details
    print("\n" + "-" * 60)
    print("Create New Admin User")
    print("-" * 60)
    
    phone = input("\nAdmin Phone Number (digits only): ").strip()
    
    # Validate phone number
    clean_phone = ''.join(filter(str.isdigit, phone))
    if not clean_phone or len(clean_phone) < 7:
        print("❌ Invalid phone number. Please enter at least 7 digits.")
        return
    
    phone = clean_phone  # Use cleaned phone number
    
    display_name = input("Display Name: ").strip()
    
    if not display_name:
        display_name = f"Admin {phone[-4:]}"
    
    password = getpass.getpass("Password (min 6 characters): ")
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        return
    
    password_confirm = getpass.getpass("Confirm Password: ")
    
    if password != password_confirm:
        print("❌ Passwords do not match")
        return
    
    # Confirm creation
    print("\n" + "-" * 60)
    print("Confirm Admin Details:")
    print("-" * 60)
    print(f"Phone:         {phone}")
    print(f"Display Name:  {display_name}")
    print(f"Organization:  {org_id}")
    print(f"Role:          admin")
    print("-" * 60)
    
    confirm = input("\nCreate this admin user? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    # Create the admin user
    success = create_admin_user(phone, password, display_name, org_id)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY")
        print("=" * 60)
        
        # Ask if they want to create another
        another = input("\nCreate another admin user? (yes/no): ").strip().lower()
        if another in ['yes', 'y']:
            main()
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED TO CREATE ADMIN USER")
        print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

