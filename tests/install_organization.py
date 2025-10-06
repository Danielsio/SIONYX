"""
Organization Installation Script
Run this once for each new organization to set up their database structure
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from services.firebase_client import FirebaseClient
from datetime import datetime
import os


def print_header(text):
    """Print styled header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def create_admin_user(client: FirebaseClient, super_admin_uid: str, super_admin_token: str):
    """Create initial admin user for the organization"""
    print_header("Create Admin User")
    
    print("This admin will be able to manage packages and users.")
    print()
    
    # Get admin details
    first_name = input("Admin First Name: ").strip()
    last_name = input("Admin Last Name: ").strip()
    phone = input("Admin Phone (e.g., 0501234567): ").strip()
    password = input("Admin Password (min 6 chars): ").strip()
    
    # Validate
    if len(password) < 6:
        print_error("Password must be at least 6 characters")
        return None
    
    # Convert phone to email
    clean_phone = ''.join(filter(str.isdigit, phone))
    email = f"{clean_phone}@sionyx.app"
    
    print()
    print_info("Creating admin account...")
    
    # Sign up - this will change client's authentication!
    result = client.sign_up(email, password)
    
    if not result.get('success'):
        print_error(f"Failed to create admin: {result.get('error')}")
        return None
    
    uid = result['uid']
    print_success(f"Admin account created (UID: {uid})")
    
    # IMPORTANT: Restore super admin authentication
    # The sign_up changed the client's auth to the new user
    # We need to restore super admin auth for subsequent operations
    client.id_token = super_admin_token
    client.user_id = super_admin_uid
    print_info(f"Restored super admin authentication")
    
    # Create admin user data
    admin_data = {
        'firstName': first_name,
        'lastName': last_name,
        'phoneNumber': phone,
        'email': '',
        'remainingTime': 0,
        'remainingPrints': 0,
        'isActive': True,
        'isAdmin': True,  # This is the important field
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat()
    }
    
    # Save to database
    db_result = client.db_set(f'users/{uid}', admin_data)
    
    if not db_result.get('success'):
        print_error(f"Failed to save admin data: {db_result.get('error')}")
        return None
    
    print_success(f"Admin user created: {first_name} {last_name}")
    print_info(f"Login with phone: {phone}")
    
    return {
        'uid': uid,
        'phone': phone,
        'password': password,
        'data': admin_data
    }


def seed_starter_packages(client: FirebaseClient):
    """Create starter packages for the organization"""
    print_header("Create Starter Packages")
    
    response = input("Create starter packages? (y/n): ").strip().lower()
    
    if response != 'y':
        print_info("Skipping package creation")
        return
    
    packages = [
        {
            "name": "Quick Session",
            "description": "Perfect for checking emails and quick tasks",
            "minutes": 30,
            "prints": 5,
            "price": 25,
            "discountPercent": 0,
            "isActive": True,
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
            "isActive": True,
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
            "isActive": True,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
    ]
    
    print()
    print_info(f"Creating {len(packages)} starter packages...")
    
    import requests
    
    for i, package in enumerate(packages, 1):
        print(f"\n  📦 Package {i}/{len(packages)}: {package['name']}")
        print(f"     Price: ₪{package['price']} | Time: {package['minutes']}min | Prints: {package['prints']}")
        
        # Push to Firebase (auto-generates ID)
        result = requests.post(
            url=f"{client.database_url}/organizations/{client.org_id}/packages.json",
            params={'auth': client.id_token},
            json=package
        )
        
        if result.status_code == 200:
            pkg_id = result.json()['name']
            print(f"     ✅ Created with ID: {pkg_id}")
        else:
            print(f"     ❌ Failed: {result.text}")
    
    print()
    print_success("Starter packages created")


def create_org_metadata(client: FirebaseClient, org_name: str):
    """Create basic organization metadata"""
    print_info("Creating organization metadata...")
    
    metadata = {
        'name': org_name,
        'createdAt': datetime.now().isoformat(),
        'status': 'active'
    }
    
    result = client.db_set('metadata', metadata)
    
    if result.get('success'):
        print_success(f"Organization metadata created: {org_name}")
        return True
    else:
        print_error(f"Failed to create metadata: {result.get('error')}")
        return False


def verify_installation(client: FirebaseClient):
    """Verify the installation was successful"""
    print_header("Verification")
    
    # Debug: Show current authentication
    print_info(f"Verifying as UID: {client.user_id}")
    print()
    
    checks = []
    
    # Check organization metadata
    metadata_result = client.db_get('metadata')
    if metadata_result.get('success') and metadata_result.get('data'):
        checks.append(('Organization metadata', True))
    else:
        checks.append(('Organization metadata', False))
    
    # Check users exist
    users_result = client.db_get('users')
    if users_result.get('success') and users_result.get('data'):
        user_count = len(users_result['data'])
        checks.append((f'Admin user ({user_count} found)', True))
    else:
        checks.append(('Admin user', False))
    
    # Check packages (optional)
    packages_result = client.db_get('packages')
    if packages_result.get('success') and packages_result.get('data'):
        pkg_count = len(packages_result['data'])
        checks.append((f'Packages ({pkg_count} found)', True))
    else:
        checks.append(('Packages (optional)', False))
    
    # Print results
    print()
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
    
    all_critical_passed = all(passed for name, passed in checks if 'optional' not in name.lower())
    
    return all_critical_passed


def main():
    """Main installation flow"""
    print_header("🚀 SIONYX Organization Installation")
    
    print("⚠️  SUPER ADMIN AUTHENTICATION REQUIRED")
    print("This script requires super admin credentials to create organizations.")
    print()
    
    # Get super admin credentials
    print_header("Super Admin Login")
    super_admin_email = input("Super Admin Email: ").strip()
    super_admin_password = input("Super Admin Password: ").strip()
    
    if not super_admin_email or not super_admin_password:
        print_error("Super admin credentials are required!")
        sys.exit(1)
    
    print()
    print_info("Authenticating as super admin...")
    
    # Temporarily set ORG_ID to a dummy value for client initialization
    # We'll override it when creating the actual organization
    os.environ['ORG_ID'] = 'temp'
    
    # Initialize Firebase client and authenticate as super admin
    try:
        client = FirebaseClient()
        auth_result = client.sign_in(super_admin_email, super_admin_password)
        
        if not auth_result.get('success'):
            print_error(f"Super admin authentication failed: {auth_result.get('error')}")
            print_info("Make sure you're using the super admin account")
            sys.exit(1)
        
        super_admin_uid = auth_result['uid']
        print_success(f"Authenticated as super admin (UID: {super_admin_uid})")
        print_info(f"Client auth UID: {client.user_id}")
        
        # Verify super admin status
        config_result = client.db_get('config/superAdminUid')
        if config_result.get('success'):
            configured_uid = config_result.get('data')
            if configured_uid and configured_uid != super_admin_uid:
                print_error(f"You are not the configured super admin!")
                print_info(f"Expected UID: {configured_uid}")
                print_info(f"Your UID: {super_admin_uid}")
                sys.exit(1)
        
        print_success("Super admin verified")
        
    except Exception as e:
        print_error(f"Failed to authenticate: {e}")
        return
    
    print()
    
    # Get organization ID from user input
    print_header("Organization Details")
    print("Enter the organization ID (lowercase, letters/numbers/hyphens only)")
    print("Examples: myorg, tech-lab, school123")
    org_id = input("Organization ID: ").strip().lower()
    
    if not org_id:
        print_error("Organization ID cannot be empty!")
        sys.exit(1)
    
    # Validate org_id format (basic validation)
    import re
    if not re.match(r'^[a-z0-9-]+$', org_id):
        print_error("Invalid organization ID format!")
        print_info("Use only lowercase letters, numbers, and hyphens")
        sys.exit(1)
    
    # Check if organization already exists
    print()
    print_info(f"Checking if organization '{org_id}' exists...")
    org_check = client.db_get(f'organizations/{org_id}')
    if org_check.get('success') and org_check.get('data'):
        print_error(f"Organization '{org_id}' already exists!")
        sys.exit(1)
    
    print()
    print(f"Organization ID: {org_id}")
    print(f"Database: {os.getenv('FIREBASE_DATABASE_URL', 'Not set')}")
    print()
    
    response = input(f"Continue with installation for '{org_id}'? (y/n): ").strip().lower()
    
    if response != 'y':
        print_info("Installation cancelled")
        return
    
    # Update client's org_id for subsequent operations
    client.org_id = org_id
    
    # Get organization display name
    org_name = input("Organization Display Name: ").strip()
    if not org_name:
        org_name = org_id.title()
    
    print()
    
    # Save super admin credentials before creating admin user
    super_admin_token = client.id_token
    super_admin_uid_saved = client.user_id
    
    # Step 1: Create org metadata
    if not create_org_metadata(client, org_name):
        print_error("Installation failed: Could not create organization metadata")
        return
    
    # Step 2: Create admin user (will restore super admin auth after)
    admin = create_admin_user(client, super_admin_uid_saved, super_admin_token)
    if not admin:
        print_error("Installation failed: Could not create admin user")
        return
    
    # Step 3: Seed packages (optional)
    seed_starter_packages(client)
    
    # Step 4: Verify installation
    print()
    success = verify_installation(client)
    
    # Final summary
    print_header("Installation Complete! 🎉")
    
    if success:
        print("Your organization is ready to use!")
        print()
        print("Next steps:")
        print(f"  1. Login with phone: {admin['phone']}")
        print(f"  2. Launch the app: python src/main.py")
        print(f"  3. Create additional users through registration")
        print()
        print("Firebase Console:")
        print(f"  https://console.firebase.google.com/")
        print(f"  Check: Realtime Database → organizations/{org_id}/")
        print()
        print_success("Installation successful!")
    else:
        print_error("Installation completed with warnings")
        print_info("Some components may not be properly configured")
        print_info("Check the verification results above")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

