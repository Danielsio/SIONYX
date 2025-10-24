#!/usr/bin/env python3
"""
SIONYX Complete Installation Script
===================================
This script will:
1. Collect Firebase and Nedarim payment credentials
2. Create an organization
3. Create an admin user
4. Seed starter packages
5. Generate a .env file with all configuration

Run this once to set up your SIONYX installation.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Colors for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text):
    """Print styled header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")


def print_step(step_num, total, text):
    """Print step indicator"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[Step {step_num}/{total}] {text}{Colors.ENDC}")


def prompt_input(prompt_text, required=True, default=None, secure=False):
    """Prompt for user input with validation"""
    while True:
        if secure:
            import getpass

            value = getpass.getpass(f"{Colors.BOLD}{prompt_text}{Colors.ENDC} ").strip()
        else:
            display_prompt = f"{Colors.BOLD}{prompt_text}{Colors.ENDC}"
            if default:
                display_prompt += f" [{default}]"
            display_prompt += ": "
            value = input(display_prompt).strip()

        if not value and default:
            return default
        if not value and required:
            print_error("This field is required!")
            continue
        return value


def validate_org_id(org_id):
    """Validate organization ID format"""
    if not re.match(r"^[a-z0-9-]+$", org_id):
        return False, "Must contain only lowercase letters, numbers, and hyphens"
    if len(org_id) < 3:
        return False, "Must be at least 3 characters long"
    if org_id.startswith("-") or org_id.endswith("-"):
        return False, "Cannot start or end with a hyphen"
    return True, "OK"


def collect_firebase_config():
    """Collect Firebase configuration"""
    print_step(1, 6, "Firebase Configuration")

    # Check if .env already exists with Firebase config
    env_path = Path(".env")
    if env_path.exists():
        print_info("Found existing .env file with Firebase configuration")
        print_info("You can reuse these credentials or enter new ones")
        print()

        # Try to read existing values
        existing_config = {}
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.startswith("FIREBASE_"):
                        existing_config[key] = value.strip()

        if existing_config.get("FIREBASE_API_KEY"):
            reuse = (
                input(
                    f"{Colors.BOLD}Use existing Firebase configuration? (y/n){Colors.ENDC} [y]: "
                )
                .strip()
                .lower()
            )
            if reuse in ["", "y", "yes"]:
                print_success("Using existing Firebase configuration")
                return existing_config

    print_info("This is your ROOT Firebase project that serves ALL organizations")
    print_info("You can find these in your Firebase Console:")
    print_info("https://console.firebase.google.com/ → Project Settings → General")
    print()

    config = {}
    config["FIREBASE_API_KEY"] = prompt_input("Firebase API Key")
    config["FIREBASE_AUTH_DOMAIN"] = prompt_input(
        "Firebase Auth Domain (e.g., your-project.firebaseapp.com)"
    )
    config["FIREBASE_DATABASE_URL"] = prompt_input(
        "Firebase Database URL (e.g., https://your-project.firebaseio.com)"
    )
    config["FIREBASE_PROJECT_ID"] = prompt_input("Firebase Project ID")

    return config


def collect_payment_config():
    """Collect Nedarim payment configuration"""
    print_step(2, 6, "Payment Gateway Configuration (Nedarim Plus)")
    print()
    print("Do you have Nedarim Plus payment gateway credentials?")
    print_info("If you don't have these yet, you can leave them empty and add later")
    print()

    has_nedarim = (
        input(f"{Colors.BOLD}Configure Nedarim now? (y/n){Colors.ENDC} [y]: ")
        .strip()
        .lower()
    )

    config = {}
    if has_nedarim in ["", "y", "yes"]:
        print()
        print_info("Get these from your Nedarim Plus account:")
        print()
        config["NEDARIM_MOSAD_ID"] = prompt_input("Nedarim Mosad ID", required=False)
        config["NEDARIM_API_VALID"] = prompt_input(
            "Nedarim API Valid Key", required=False, secure=True
        )
        config["NEDARIM_CALLBACK_URL"] = prompt_input(
            "Nedarim Callback URL (Firebase Function URL)", required=False
        )

        if not config["NEDARIM_MOSAD_ID"]:
            print_warning(
                "Payment features will be disabled until you add Nedarim credentials"
            )
    else:
        print_warning("Skipping payment configuration. You can add it to .env later")
        config["NEDARIM_MOSAD_ID"] = ""
        config["NEDARIM_API_VALID"] = ""
        config["NEDARIM_CALLBACK_URL"] = ""

    return config


def collect_organization_info():
    """Collect organization information"""
    print_step(3, 6, "Organization Setup")
    print()
    print(
        "The Organization ID uniquely identifies this organization in the shared database."
    )
    print_info("Multiple organizations can exist in the same Firebase project")
    print_info("Examples: tech-lab, school123, mycompany")
    print_warning("Once created, this cannot be changed!")
    print()

    while True:
        org_id = prompt_input(
            "Organization ID (lowercase, letters/numbers/hyphens)"
        ).lower()
        valid, message = validate_org_id(org_id)

        if not valid:
            print_error(f"Invalid Organization ID: {message}")
            continue

        break

    org_name = prompt_input(
        "Organization Display Name", default=org_id.replace("-", " ").title()
    )

    return {"org_id": org_id, "org_name": org_name}


def collect_admin_info():
    """Collect admin user information"""
    print_step(4, 6, "Admin User Creation")
    print()
    print("Create the first admin user for your organization.")
    print_info(
        "This user will be able to manage packages and view users via the admin dashboard"
    )
    print()

    admin = {}
    admin["first_name"] = prompt_input("Admin First Name")
    admin["last_name"] = prompt_input("Admin Last Name")
    admin["phone"] = prompt_input("Admin Phone Number (digits only, e.g., 0501234567)")

    # Validate phone
    admin["phone"] = "".join(filter(str.isdigit, admin["phone"]))
    if len(admin["phone"]) < 7:
        print_error("Invalid phone number")
        sys.exit(1)

    while True:
        password = prompt_input("Admin Password (min 6 characters)", secure=True)
        if len(password) < 6:
            print_error("Password must be at least 6 characters")
            continue

        password_confirm = prompt_input("Confirm Password", secure=True)
        if password != password_confirm:
            print_error("Passwords do not match")
            continue

        admin["password"] = password
        break

    return admin


def confirm_installation(firebase_config, payment_config, org_info, admin_info):
    """Display summary and confirm installation"""
    print_header("Installation Summary")

    print(f"{Colors.BOLD}Firebase:{Colors.ENDC}")
    print(f"  Project ID: {firebase_config['FIREBASE_PROJECT_ID']}")
    print(f"  Database: {firebase_config['FIREBASE_DATABASE_URL']}")
    print()

    print(f"{Colors.BOLD}Payment:{Colors.ENDC}")
    if payment_config.get("NEDARIM_MOSAD_ID"):
        print(f"  Nedarim Mosad ID: {payment_config['NEDARIM_MOSAD_ID']}")
        print(
            f"  Callback URL: {payment_config.get('NEDARIM_CALLBACK_URL', 'Not set')}"
        )
    else:
        print(f"  {Colors.YELLOW}Not configured (can be added later){Colors.ENDC}")
    print()

    print(f"{Colors.BOLD}Organization:{Colors.ENDC}")
    print(f"  ID: {org_info['org_id']}")
    print(f"  Name: {org_info['org_name']}")
    print()

    print(f"{Colors.BOLD}Admin User:{Colors.ENDC}")
    print(f"  Name: {admin_info['first_name']} {admin_info['last_name']}")
    print(f"  Phone: {admin_info['phone']}")
    print()

    confirm = (
        input(f"{Colors.BOLD}Proceed with installation? (yes/no){Colors.ENDC}: ")
        .strip()
        .lower()
    )
    return confirm in ["yes", "y"]


def create_env_file(firebase_config, payment_config, org_id):
    """Create .env file with all configuration"""
    print_step(5, 6, "Creating .env Configuration File")

    env_content = f"""# SIONYX Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# DO NOT COMMIT THIS FILE TO VERSION CONTROL!

# ============================================================================
# Organization Configuration
# ============================================================================
ORG_ID={org_id}

# ============================================================================
# Firebase Configuration
# ============================================================================
FIREBASE_API_KEY={firebase_config['FIREBASE_API_KEY']}
FIREBASE_AUTH_DOMAIN={firebase_config['FIREBASE_AUTH_DOMAIN']}
FIREBASE_DATABASE_URL={firebase_config['FIREBASE_DATABASE_URL']}
FIREBASE_PROJECT_ID={firebase_config['FIREBASE_PROJECT_ID']}

# ============================================================================
# Payment Gateway Configuration (Nedarim Plus)
# ============================================================================
NEDARIM_MOSAD_ID={payment_config.get('NEDARIM_MOSAD_ID', '')}
NEDARIM_API_VALID={payment_config.get('NEDARIM_API_VALID', '')}
NEDARIM_CALLBACK_URL={payment_config.get('NEDARIM_CALLBACK_URL', '')}

# ============================================================================
# Notes:
# - Keep this file secure and never share it publicly
# - Make sure .env is in your .gitignore
# - To change organization, you must reinstall or manually edit this file
# ============================================================================
"""

    env_path = Path(__file__).parent / ".env"

    # Check if .env already exists
    if env_path.exists():
        backup_path = env_path.with_suffix(".env.backup")
        print_warning(
            f".env file already exists! Creating backup at {backup_path.name}"
        )
        import shutil

        shutil.copy(env_path, backup_path)

    # Write .env file
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print_success(f".env file created at {env_path}")
    print_info("Make sure .env is in your .gitignore!")

    return env_path


def setup_firebase_client(firebase_config, org_id):
    """Set up Firebase client with configuration"""
    # Set environment variables temporarily for Firebase client
    os.environ["FIREBASE_API_KEY"] = firebase_config["FIREBASE_API_KEY"]
    os.environ["FIREBASE_AUTH_DOMAIN"] = firebase_config["FIREBASE_AUTH_DOMAIN"]
    os.environ["FIREBASE_DATABASE_URL"] = firebase_config["FIREBASE_DATABASE_URL"]
    os.environ["FIREBASE_PROJECT_ID"] = firebase_config["FIREBASE_PROJECT_ID"]
    os.environ["ORG_ID"] = org_id

    # Add src to path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    from services.firebase_client import FirebaseClient

    return FirebaseClient()


def create_organization_and_admin(firebase_config, org_info, admin_info):
    """Create organization and admin user in Firebase"""
    print_step(6, 6, "Creating Organization and Admin User")
    print()

    # Authenticate as super admin
    print_info("Super Admin authentication required...")
    print()
    super_admin_email = prompt_input("Super Admin Email")
    super_admin_password = prompt_input("Super Admin Password", secure=True)

    print()
    print_info("Connecting to Firebase...")

    try:
        client = setup_firebase_client(firebase_config, org_info["org_id"])

        # Authenticate
        auth_result = client.sign_in(super_admin_email, super_admin_password)
        if not auth_result.get("success"):
            print_error(f"Authentication failed: {auth_result.get('error')}")
            return False

        super_admin_uid = auth_result["uid"]
        super_admin_token = client.id_token
        print_success(f"Authenticated as super admin (UID: {super_admin_uid})")

        # Verify super admin
        config_result = client.db_get("config/superAdminUid")
        if config_result.get("success"):
            configured_uid = config_result.get("data")
            if configured_uid and configured_uid != super_admin_uid:
                print_error("You are not the configured super admin!")
                return False

        print_success("Super admin verified")
        print()

        # Check if organization exists
        print_info(f"Checking if organization '{org_info['org_id']}' exists...")
        org_check = client.db_get(f"organizations/{org_info['org_id']}")
        if org_check.get("success") and org_check.get("data"):
            print_error(f"Organization '{org_info['org_id']}' already exists!")
            return False

        # Create organization metadata
        print_info("Creating organization metadata...")
        metadata = {
            "name": org_info["org_name"],
            "createdAt": datetime.now().isoformat(),
            "status": "active",
        }

        result = client.db_set("metadata", metadata)
        if not result.get("success"):
            print_error(f"Failed to create organization: {result.get('error')}")
            return False

        print_success(f"Organization '{org_info['org_name']}' created")
        print()

        # Create admin user
        print_info("Creating admin user...")

        # Convert phone to email
        clean_phone = "".join(filter(str.isdigit, admin_info["phone"]))
        email = f"{clean_phone}@sionyx.app"

        # Sign up admin
        signup_result = client.sign_up(email, admin_info["password"])
        if not signup_result.get("success"):
            print_error(f"Failed to create admin: {signup_result.get('error')}")
            return False

        admin_uid = signup_result["uid"]
        print_success(f"Admin account created (UID: {admin_uid})")

        # Restore super admin auth
        client.id_token = super_admin_token
        client.user_id = super_admin_uid

        # Save admin data
        admin_data = {
            "firstName": admin_info["first_name"],
            "lastName": admin_info["last_name"],
            "phoneNumber": admin_info["phone"],
            "email": "",
            "remainingTime": 0,
            "remainingPrints": 0.0,  # Start with 0 NIS print budget (renamed from count)
            "isActive": True,
            "isAdmin": True,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        db_result = client.db_set(f"users/{admin_uid}", admin_data)
        if not db_result.get("success"):
            print_error(f"Failed to save admin data: {db_result.get('error')}")
            return False

        print_success(
            f"Admin user created: {admin_info['first_name']} {admin_info['last_name']}"
        )
        print()

        # Seed starter packages
        create_starter_packages(client)

        return True

    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_starter_packages(client):
    """Create starter packages"""
    print_info("Creating starter packages...")

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
            "updatedAt": datetime.now().isoformat(),
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
            "updatedAt": datetime.now().isoformat(),
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
            "updatedAt": datetime.now().isoformat(),
        },
    ]

    import requests

    for i, package in enumerate(packages, 1):
        result = requests.post(
            url=f"{client.database_url}/organizations/{client.org_id}/packages.json",
            params={"auth": client.id_token},
            json=package,
        )

        if result.status_code == 200:
            print_success(f"Package {i}/3: {package['name']} (₪{package['price']})")
        else:
            print_warning(f"Failed to create package: {package['name']}")


def print_final_instructions(org_info, admin_info, env_path):
    """Print final instructions"""
    print_header("🎉 Installation Complete!")

    print(
        f"{Colors.GREEN}{Colors.BOLD}Organization '{org_info['org_name']}' is ready!{Colors.ENDC}\n"
    )

    print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print(
        f"  1. Install dependencies: {Colors.CYAN}pip install -r requirements.txt{Colors.ENDC}"
    )
    print(f"  2. Launch the application: {Colors.CYAN}python src/main.py{Colors.ENDC}")
    print()

    print(f"{Colors.BOLD}Admin Login:{Colors.ENDC}")
    print(f"  Phone: {admin_info['phone']}")
    print(f"  Password: (the one you set)")
    print()

    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  Environment File: {env_path}")
    print(f"  Organization ID: {org_info['org_id']}")
    print(f"  Database Path: organizations/{org_info['org_id']}/")
    print()

    print(f"{Colors.BOLD}Admin Dashboard:{Colors.ENDC}")
    print(f"  1. Navigate to: {Colors.CYAN}cd admin-dashboard{Colors.ENDC}")
    print(f"  2. Install: {Colors.CYAN}npm install{Colors.ENDC}")
    print(
        f"  3. Update config: {Colors.CYAN}src/config/firebase.js{Colors.ENDC} (use same Firebase credentials)"
    )
    print(f"  4. Run: {Colors.CYAN}npm run dev{Colors.ENDC}")
    print()

    print(f"{Colors.BOLD}Firebase Console:{Colors.ENDC}")
    print(f"  https://console.firebase.google.com/")
    print(f"  Navigate: Realtime Database → organizations → {org_info['org_id']}")
    print()

    print(f"{Colors.CYAN}ℹ️  Multi-Organization Setup:{Colors.ENDC}")
    print(f"  To add another organization to the SAME Firebase project:")
    print(f"  1. Run: {Colors.CYAN}python install.py{Colors.ENDC} again")
    print(f"  2. Use the SAME Firebase credentials")
    print(f"  3. Choose a DIFFERENT organization ID")
    print(f"  4. Keep separate .env files (e.g., .env.org1, .env.org2)")
    print()

    print(f"{Colors.YELLOW}⚠️  Security Reminders:{Colors.ENDC}")
    print(f"  • Never commit .env to version control")
    print(f"  • Keep your super admin credentials secure")
    print(f"  • All organizations share the same Firebase project")
    print(f"  • Data isolation is managed by ORG_ID in the database path")
    print()

    print_success("Installation successful! Happy coding! 🚀")


def main():
    """Main installation flow"""
    try:
        print_header("🚀 SIONYX Organization Setup")
        print(
            f"{Colors.BOLD}This wizard will set up a new organization in your SIONYX system{Colors.ENDC}\n"
        )

        print(f"{Colors.CYAN}Architecture Overview:{Colors.ENDC}")
        print("  • ONE Firebase project serves ALL organizations")
        print("  • Each organization has a unique ID (e.g., tech-lab, school123)")
        print("  • Data is isolated by organization ID in the database")
        print(
            "  • You can run this installer multiple times for different organizations"
        )
        print()

        print("What this script will do:")
        print("  ✓ Configure Firebase connection (or reuse existing)")
        print("  ✓ Configure payment gateway (optional)")
        print("  ✓ Create organization in database")
        print("  ✓ Create admin user")
        print("  ✓ Seed starter packages")
        print("  ✓ Generate .env file")
        print()

        ready = (
            input(f"{Colors.BOLD}Ready to begin? (yes/no){Colors.ENDC}: ")
            .strip()
            .lower()
        )
        if ready not in ["yes", "y"]:
            print_info("Installation cancelled")
            return

        # Collect all information
        firebase_config = collect_firebase_config()
        payment_config = collect_payment_config()
        org_info = collect_organization_info()
        admin_info = collect_admin_info()

        # Confirm
        if not confirm_installation(
            firebase_config, payment_config, org_info, admin_info
        ):
            print_info("Installation cancelled")
            return

        # Create .env file
        env_path = create_env_file(firebase_config, payment_config, org_info["org_id"])

        # Create organization and admin in Firebase
        success = create_organization_and_admin(firebase_config, org_info, admin_info)

        if success:
            print_final_instructions(org_info, admin_info, env_path)
        else:
            print_error("Installation failed!")
            print_info("Your .env file was created, but organization setup failed.")
            print_info(
                "You may need to run the installation again or manually fix the issue."
            )

    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}❌ Installation cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
