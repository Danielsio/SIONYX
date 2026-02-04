#!/usr/bin/env python3
"""
Supervisor Management Script

Manages supervisor users and supervisor mode for organizations.

Usage:
    python scripts/manage_supervisor.py list
    python scripts/manage_supervisor.py show --org <orgId>
    python scripts/manage_supervisor.py create --org <orgId> --phone <phone> --password <password> [--name <name>]
    python scripts/manage_supervisor.py promote --org <orgId> --phone <phone>
    python scripts/manage_supervisor.py disable --org <orgId>
    python scripts/manage_supervisor.py enable --org <orgId>

Examples:
    # List all organizations and their supervisor status
    python scripts/manage_supervisor.py list

    # Create a new supervisor user for an organization
    python scripts/manage_supervisor.py create --org "myOrg" --phone "0501234567" --password "TempPass123!" --name "John Doe"

    # Promote an existing user to supervisor
    python scripts/manage_supervisor.py promote --org "myOrg" --phone "0501234567"

    # Disable supervisor mode for an org (keeps user role, disables features)
    python scripts/manage_supervisor.py disable --org "myOrg"

    # Re-enable supervisor mode
    python scripts/manage_supervisor.py enable --org "myOrg"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import firebase_admin
    from firebase_admin import auth, credentials, db
except ImportError:
    print("Error: firebase-admin package not installed.")
    print("Install with: pip install firebase-admin")
    sys.exit(1)

# Platform-specific output handling
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    # Use plain ASCII on Windows to avoid encoding issues
    CHECK = "[OK]"
    CROSS = "[X]"
    WARN = "[!]"
    INFO = "[i]"
    ARROW = "->"
    
    def green(text): return text
    def red(text): return text
    def yellow(text): return text
    def blue(text): return text
    def bold(text): return text
    def dim(text): return text
else:
    CHECK = "✓"
    CROSS = "✗"
    WARN = "⚠"
    INFO = "ℹ"
    ARROW = "→"
    
    def green(text): return f"\033[92m{text}\033[0m"
    def red(text): return f"\033[91m{text}\033[0m"
    def yellow(text): return f"\033[93m{text}\033[0m"
    def blue(text): return f"\033[94m{text}\033[0m"
    def bold(text): return f"\033[1m{text}\033[0m"
    def dim(text): return f"\033[2m{text}\033[0m"


def find_service_account() -> Optional[str]:
    """Find service account key file."""
    search_paths = [
        project_root / "serviceAccountKey.json",
        project_root / "service-account.json",
        project_root / "firebase-adminsdk.json",
        Path.home() / ".config" / "firebase" / "serviceAccountKey.json",
    ]
    
    for path in search_paths:
        if path.exists():
            return str(path)
    
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and Path(env_path).exists():
        return env_path
    
    return None


def load_database_url() -> Optional[str]:
    """Load database URL from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("FIREBASE_DATABASE_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return url
    return None


def initialize_firebase() -> bool:
    """Initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        return True
    
    service_account_path = find_service_account()
    if not service_account_path:
        print(red(f"{CROSS} Service account key not found."))
        print("  Place serviceAccountKey.json in project root or set GOOGLE_APPLICATION_CREDENTIALS")
        return False
    
    database_url = load_database_url()
    if not database_url:
        print(red(f"{CROSS} Database URL not found in .env"))
        return False
    
    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        print(green(f"{CHECK} Firebase initialized"))
        return True
    except Exception as e:
        print(red(f"{CROSS} Failed to initialize Firebase: {e}"))
        return False


def phone_to_email(phone: str) -> str:
    """Convert phone number to email format used by the system."""
    # Remove any non-digit characters
    clean_phone = ''.join(filter(str.isdigit, phone))
    return f"{clean_phone}@sionyx.app"


def get_all_organizations() -> List[Dict[str, Any]]:
    """Get all organizations and their metadata."""
    try:
        orgs_ref = db.reference("organizations")
        orgs_data = orgs_ref.get() or {}
        
        result = []
        for org_id, org_data in orgs_data.items():
            metadata = org_data.get("metadata", {})
            settings = metadata.get("settings", {})
            users = org_data.get("users", {})
            
            # Find supervisor(s) in this org
            supervisors = []
            for user_id, user_data in users.items():
                if user_data.get("role") == "supervisor":
                    supervisors.append({
                        "userId": user_id,
                        "phone": user_data.get("phone", "unknown"),
                        "name": user_data.get("name", ""),
                    })
            
            result.append({
                "orgId": org_id,
                "name": metadata.get("name", org_id),
                "supervisorEnabled": settings.get("supervisorEnabled", False),
                "supervisors": supervisors,
                "userCount": len(users),
            })
        
        return result
    except Exception as e:
        print(red(f"{CROSS} Error fetching organizations: {e}"))
        return []


def get_organization_details(org_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed info about a specific organization."""
    try:
        org_ref = db.reference(f"organizations/{org_id}")
        org_data = org_ref.get()
        
        if not org_data:
            return None
        
        metadata = org_data.get("metadata", {})
        settings = metadata.get("settings", {})
        users = org_data.get("users", {})
        
        # Find all supervisors
        supervisors = []
        admins = []
        for user_id, user_data in users.items():
            role = user_data.get("role", "user")
            if user_data.get("isAdmin") and not user_data.get("role"):
                role = "admin (legacy)"
            
            user_info = {
                "userId": user_id,
                "phone": user_data.get("phone", "unknown"),
                "name": user_data.get("name", ""),
                "role": role,
            }
            
            if user_data.get("role") == "supervisor":
                supervisors.append(user_info)
            elif user_data.get("role") == "admin" or user_data.get("isAdmin"):
                admins.append(user_info)
        
        return {
            "orgId": org_id,
            "name": metadata.get("name", org_id),
            "supervisorEnabled": settings.get("supervisorEnabled", False),
            "operatingHours": settings.get("operatingHours", {}),
            "supervisors": supervisors,
            "admins": admins,
            "userCount": len(users),
        }
    except Exception as e:
        print(red(f"{CROSS} Error fetching organization: {e}"))
        return None


def find_user_by_phone(org_id: str, phone: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Find a user in an organization by phone number."""
    try:
        users_ref = db.reference(f"organizations/{org_id}/users")
        users = users_ref.get() or {}
        
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        for user_id, user_data in users.items():
            user_phone = ''.join(filter(str.isdigit, user_data.get("phone", "")))
            if user_phone == clean_phone:
                return (user_id, user_data)
        
        return None
    except Exception as e:
        print(red(f"{CROSS} Error finding user: {e}"))
        return None


def create_supervisor(org_id: str, phone: str, password: str, name: str = "") -> bool:
    """Create a new supervisor user for an organization."""
    email = phone_to_email(phone)
    
    print(f"\n{INFO} Creating supervisor for org: {bold(org_id)}")
    print(f"   Phone: {phone}")
    print(f"   Email: {email}")
    if name:
        print(f"   Name: {name}")
    
    # Check if org exists
    org_ref = db.reference(f"organizations/{org_id}/metadata")
    if not org_ref.get():
        print(red(f"\n{CROSS} Organization '{org_id}' not found"))
        return False
    
    # Check if user already exists in this org
    existing = find_user_by_phone(org_id, phone)
    if existing:
        user_id, user_data = existing
        print(yellow(f"\n{WARN} User already exists in this org"))
        print(f"   Current role: {user_data.get('role', user_data.get('isAdmin', 'user'))}")
        
        confirm = input(f"\nPromote this user to supervisor? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return False
        
        return promote_user_to_supervisor(org_id, user_id, name)
    
    # Create Firebase Auth user
    try:
        print(f"\n{ARROW} Creating Firebase Auth user...")
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=name or phone,
        )
        user_id = user_record.uid
        print(green(f"   {CHECK} Auth user created: {user_id}"))
    except auth.EmailAlreadyExistsError:
        print(yellow(f"\n{WARN} Auth user already exists, fetching..."))
        try:
            user_record = auth.get_user_by_email(email)
            user_id = user_record.uid
            print(f"   Found user: {user_id}")
        except Exception as e:
            print(red(f"{CROSS} Failed to get existing user: {e}"))
            return False
    except Exception as e:
        print(red(f"{CROSS} Failed to create auth user: {e}"))
        return False
    
    # Create user record in database
    try:
        print(f"{ARROW} Creating user record in database...")
        user_ref = db.reference(f"organizations/{org_id}/users/{user_id}")
        
        user_data = {
            "phone": phone,
            "name": name,
            "role": "supervisor",
            "isAdmin": True,  # Backwards compatibility
            "createdAt": datetime.now().isoformat(),
            "createdBy": "manage_supervisor script",
            "remainingTime": 0,
            "printBalance": 0,
        }
        
        user_ref.set(user_data)
        print(green(f"   {CHECK} User record created"))
    except Exception as e:
        print(red(f"{CROSS} Failed to create user record: {e}"))
        return False
    
    # Enable supervisor mode for org
    try:
        print(f"{ARROW} Enabling supervisor mode for org...")
        settings_ref = db.reference(f"organizations/{org_id}/metadata/settings")
        settings_ref.update({
            "supervisorEnabled": True,
            "supervisorEnabledAt": datetime.now().isoformat(),
        })
        print(green(f"   {CHECK} Supervisor mode enabled"))
    except Exception as e:
        print(red(f"{CROSS} Failed to enable supervisor mode: {e}"))
        return False
    
    print(green(f"\n{CHECK} Supervisor created successfully!"))
    print(f"\n   Login credentials:")
    print(f"   Phone: {phone}")
    print(f"   Password: {password}")
    print(f"   Org ID: {org_id}")
    
    return True


def promote_user_to_supervisor(org_id: str, user_id: str, name: str = "") -> bool:
    """Promote an existing user to supervisor role."""
    try:
        print(f"\n{ARROW} Promoting user to supervisor...")
        user_ref = db.reference(f"organizations/{org_id}/users/{user_id}")
        
        update_data = {
            "role": "supervisor",
            "isAdmin": True,
            "promotedToSupervisorAt": datetime.now().isoformat(),
        }
        if name:
            update_data["name"] = name
        
        user_ref.update(update_data)
        print(green(f"   {CHECK} User promoted to supervisor"))
        
        # Enable supervisor mode
        settings_ref = db.reference(f"organizations/{org_id}/metadata/settings")
        settings_ref.update({
            "supervisorEnabled": True,
            "supervisorEnabledAt": datetime.now().isoformat(),
        })
        print(green(f"   {CHECK} Supervisor mode enabled"))
        
        return True
    except Exception as e:
        print(red(f"{CROSS} Failed to promote user: {e}"))
        return False


def promote_by_phone(org_id: str, phone: str) -> bool:
    """Promote an existing user to supervisor by phone number."""
    print(f"\n{INFO} Looking for user with phone: {phone}")
    
    existing = find_user_by_phone(org_id, phone)
    if not existing:
        print(red(f"\n{CROSS} User not found in org '{org_id}'"))
        return False
    
    user_id, user_data = existing
    print(f"   Found: {user_data.get('name', 'unnamed')} ({user_id})")
    print(f"   Current role: {user_data.get('role', 'user')}")
    
    if user_data.get("role") == "supervisor":
        print(yellow(f"\n{WARN} User is already a supervisor"))
        return True
    
    return promote_user_to_supervisor(org_id, user_id)


def set_supervisor_mode(org_id: str, enabled: bool) -> bool:
    """Enable or disable supervisor mode for an organization."""
    action = "Enabling" if enabled else "Disabling"
    print(f"\n{ARROW} {action} supervisor mode for org: {org_id}")
    
    try:
        # Check org exists
        org_ref = db.reference(f"organizations/{org_id}/metadata")
        if not org_ref.get():
            print(red(f"\n{CROSS} Organization '{org_id}' not found"))
            return False
        
        settings_ref = db.reference(f"organizations/{org_id}/metadata/settings")
        settings_ref.update({
            "supervisorEnabled": enabled,
            f"supervisor{'Enabled' if enabled else 'Disabled'}At": datetime.now().isoformat(),
        })
        
        status = "enabled" if enabled else "disabled"
        print(green(f"\n{CHECK} Supervisor mode {status} for org '{org_id}'"))
        return True
    except Exception as e:
        print(red(f"{CROSS} Failed to update supervisor mode: {e}"))
        return False


def cmd_list(args):
    """List all organizations and their supervisor status."""
    print(f"\n{bold('Organizations and Supervisor Status')}")
    print("=" * 70)
    
    orgs = get_all_organizations()
    if not orgs:
        print("No organizations found.")
        return
    
    for org in sorted(orgs, key=lambda x: x["orgId"]):
        status = green(f"{CHECK} Enabled") if org["supervisorEnabled"] else dim("Disabled")
        
        print(f"\n{bold(org['orgId'])}")
        print(f"  Name: {org['name']}")
        print(f"  Supervisor Mode: {status}")
        print(f"  Users: {org['userCount']}")
        
        if org["supervisors"]:
            print(f"  Supervisors:")
            for sup in org["supervisors"]:
                name = sup.get("name") or "unnamed"
                print(f"    - {sup['phone']} ({name})")
        else:
            print(dim(f"  Supervisors: none"))
    
    print(f"\n{'=' * 70}")
    print(f"Total: {len(orgs)} organizations")


def cmd_show(args):
    """Show details about a specific organization."""
    org_id = args.org
    
    print(f"\n{bold(f'Organization: {org_id}')}")
    print("=" * 70)
    
    details = get_organization_details(org_id)
    if not details:
        print(red(f"Organization '{org_id}' not found"))
        return
    
    status = green(f"{CHECK} Enabled") if details["supervisorEnabled"] else yellow("Disabled")
    
    print(f"Name: {details['name']}")
    print(f"Supervisor Mode: {status}")
    print(f"Total Users: {details['userCount']}")
    
    print(f"\n{bold('Supervisors:')}")
    if details["supervisors"]:
        for sup in details["supervisors"]:
            print(f"  - {sup['phone']} | {sup.get('name', 'unnamed')} | {sup['userId']}")
    else:
        print(dim("  No supervisors"))
    
    print(f"\n{bold('Admins:')}")
    if details["admins"]:
        for admin in details["admins"]:
            print(f"  - {admin['phone']} | {admin.get('name', 'unnamed')} | {admin['role']}")
    else:
        print(dim("  No admins"))
    
    if details.get("operatingHours"):
        oh = details["operatingHours"]
        print(f"\n{bold('Operating Hours:')}")
        print(f"  Enabled: {oh.get('enabled', False)}")
        print(f"  Hours: {oh.get('startTime', 'N/A')} - {oh.get('endTime', 'N/A')}")
        print(f"  Grace Period: {oh.get('gracePeriodMinutes', 5)} minutes")


def cmd_create(args):
    """Create a new supervisor user."""
    success = create_supervisor(
        org_id=args.org,
        phone=args.phone,
        password=args.password,
        name=args.name or "",
    )
    sys.exit(0 if success else 1)


def cmd_promote(args):
    """Promote an existing user to supervisor."""
    success = promote_by_phone(args.org, args.phone)
    sys.exit(0 if success else 1)


def cmd_enable(args):
    """Enable supervisor mode for an org."""
    success = set_supervisor_mode(args.org, True)
    sys.exit(0 if success else 1)


def cmd_disable(args):
    """Disable supervisor mode for an org."""
    success = set_supervisor_mode(args.org, False)
    sys.exit(0 if success else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage supervisor users and supervisor mode for organizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List all organizations and their supervisor status")
    list_parser.set_defaults(func=cmd_list)
    
    # show command
    show_parser = subparsers.add_parser("show", help="Show details about a specific organization")
    show_parser.add_argument("--org", required=True, help="Organization ID")
    show_parser.set_defaults(func=cmd_show)
    
    # create command
    create_parser = subparsers.add_parser("create", help="Create a new supervisor user")
    create_parser.add_argument("--org", required=True, help="Organization ID")
    create_parser.add_argument("--phone", required=True, help="Phone number (e.g., 0501234567)")
    create_parser.add_argument("--password", required=True, help="Initial password")
    create_parser.add_argument("--name", help="Supervisor name (optional)")
    create_parser.set_defaults(func=cmd_create)
    
    # promote command
    promote_parser = subparsers.add_parser("promote", help="Promote an existing user to supervisor")
    promote_parser.add_argument("--org", required=True, help="Organization ID")
    promote_parser.add_argument("--phone", required=True, help="Phone number of existing user")
    promote_parser.set_defaults(func=cmd_promote)
    
    # enable command
    enable_parser = subparsers.add_parser("enable", help="Enable supervisor mode for an org")
    enable_parser.add_argument("--org", required=True, help="Organization ID")
    enable_parser.set_defaults(func=cmd_enable)
    
    # disable command
    disable_parser = subparsers.add_parser("disable", help="Disable supervisor mode for an org")
    disable_parser.add_argument("--org", required=True, help="Organization ID")
    disable_parser.set_defaults(func=cmd_disable)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize Firebase
    if not initialize_firebase():
        sys.exit(1)
    
    # Run the command
    args.func(args)


if __name__ == "__main__":
    main()
