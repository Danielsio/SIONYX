#!/usr/bin/env python3
"""
Migrate User Roles from isAdmin to role field

This script migrates users from the legacy isAdmin boolean field to the new
role-based access control (RBAC) system using Firebase Admin SDK.

Migration logic:
- isAdmin: true -> role: "admin"
- isAdmin: false (or missing) -> role: "user"
- If role field already exists, skip that user

Usage:
    # Dry run (preview changes without applying)
    python scripts/migrate_roles.py --dry-run
    
    # Apply migration
    python scripts/migrate_roles.py --apply
    
    # Migrate specific organization only
    python scripts/migrate_roles.py --apply --org-id my-org
    
Requirements:
    - firebase-admin package: pip install firebase-admin
    - serviceAccountKey.json in project root (or specify with --cred-path)
"""

import argparse
import json
import os
import sys
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ANSI colors for output (disabled on Windows for encoding compatibility)
if platform.system() == "Windows":
    class Colors:
        GREEN = ""
        YELLOW = ""
        RED = ""
        BLUE = ""
        RESET = ""
        BOLD = ""
    
    def print_success(msg: str):
        print(f"[OK] {msg}")
    
    def print_warning(msg: str):
        print(f"[WARN] {msg}")
    
    def print_error(msg: str):
        print(f"[ERROR] {msg}")
    
    def print_info(msg: str):
        print(f"[INFO] {msg}")
else:
    class Colors:
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
        BOLD = "\033[1m"
    
    def print_success(msg: str):
        print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")
    
    def print_warning(msg: str):
        print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")
    
    def print_error(msg: str):
        print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")
    
    def print_info(msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")


# Try to import firebase-admin
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False


def find_service_account():
    """Find service account key file."""
    # Look in common locations
    locations = [
        Path(__file__).parent.parent / "serviceAccountKey.json",
        Path(__file__).parent.parent / "service-account.json",
        Path(__file__).parent.parent / "firebase-adminsdk.json",
        Path.home() / ".config" / "firebase" / "serviceAccountKey.json",
    ]
    
    for path in locations:
        if path.exists():
            return str(path)
    
    # Check environment variable
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and Path(env_path).exists():
        return env_path
    
    return None


def load_database_url():
    """Load database URL from .env file or environment."""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass
    
    return os.environ.get("FIREBASE_DATABASE_URL")


def init_firebase(cred_path: Optional[str] = None, database_url: Optional[str] = None):
    """Initialize Firebase Admin SDK."""
    if not FIREBASE_ADMIN_AVAILABLE:
        print_error("firebase-admin package not installed.")
        print_info("Install with: pip install firebase-admin")
        sys.exit(1)
    
    if firebase_admin._apps:
        # Already initialized
        return
    
    # Find credentials
    if not cred_path:
        cred_path = find_service_account()
    
    if not cred_path:
        print_error("No Firebase service account credentials found.")
        print_info("Place serviceAccountKey.json in project root or use --cred-path")
        sys.exit(1)
    
    print_info(f"Using credentials: {cred_path}")
    
    # Get database URL
    if not database_url:
        database_url = load_database_url()
    
    if not database_url:
        print_error("No database URL found.")
        print_info("Set FIREBASE_DATABASE_URL in .env or use --database-url")
        sys.exit(1)
    
    print_info(f"Database URL: {database_url}")
    
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        print_success("Firebase initialized")
    except Exception as e:
        print_error(f"Failed to initialize Firebase: {e}")
        sys.exit(1)


def get_organizations() -> List[str]:
    """Get list of all organization IDs."""
    try:
        ref = db.reference("organizations")
        orgs = ref.get() or {}
        return list(orgs.keys())
    except Exception as e:
        print_error(f"Failed to get organizations: {e}")
        return []


def get_users(org_id: str) -> Dict[str, Any]:
    """Get all users for an organization."""
    try:
        ref = db.reference(f"organizations/{org_id}/users")
        return ref.get() or {}
    except Exception as e:
        print_error(f"Failed to get users for {org_id}: {e}")
        return {}


def migrate_user(
    org_id: str,
    user_id: str,
    user_data: Dict[str, Any],
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Migrate a single user to the new role system.
    
    Returns dict with migration result.
    """
    result = {
        "user_id": user_id,
        "org_id": org_id,
        "action": None,
        "old_value": None,
        "new_value": None,
        "skipped": False,
        "error": None,
    }
    
    # Check if already migrated
    if "role" in user_data and user_data["role"]:
        result["action"] = "skip"
        result["skipped"] = True
        result["old_value"] = f"role={user_data['role']}"
        return result
    
    # Determine new role based on isAdmin
    is_admin = user_data.get("isAdmin", False)
    new_role = "admin" if is_admin else "user"
    
    result["old_value"] = f"isAdmin={is_admin}"
    result["new_value"] = f"role={new_role}"
    result["action"] = "migrate"
    
    if not dry_run:
        try:
            # Apply the migration
            ref = db.reference(f"organizations/{org_id}/users/{user_id}")
            ref.update({
                "role": new_role,
                "roleMigratedAt": datetime.now().isoformat(),
            })
        except Exception as e:
            result["error"] = str(e)
    
    return result


def run_migration(
    dry_run: bool = True,
    org_id: Optional[str] = None,
    verbose: bool = False
):
    """Run the migration."""
    print()
    title = "DRY RUN - Role Migration" if dry_run else "Role Migration"
    print(f"{Colors.BOLD}{title}{Colors.RESET}")
    print("=" * 50)
    
    # Get organizations to migrate
    if org_id:
        org_ids = [org_id]
        print_info(f"Migrating single organization: {org_id}")
    else:
        org_ids = get_organizations()
        print_info(f"Found {len(org_ids)} organizations")
    
    if not org_ids:
        print_error("No organizations found!")
        return False
    
    # Statistics
    total_users = 0
    migrated = 0
    skipped = 0
    errors = 0
    
    for org in org_ids:
        print()
        print(f"{Colors.BOLD}Organization: {org}{Colors.RESET}")
        
        users = get_users(org)
        if not users:
            print_warning("No users found")
            continue
            
        print_info(f"Found {len(users)} users")
        
        for user_id, user_data in users.items():
            if not isinstance(user_data, dict):
                print_warning(f"  Skipping invalid user data: {user_id}")
                continue
                
            total_users += 1
            
            result = migrate_user(org, user_id, user_data, dry_run)
            
            if result.get("error"):
                errors += 1
                print_error(f"  Error: {user_id} - {result['error']}")
            elif result["skipped"]:
                skipped += 1
                if verbose:
                    print(f"  Skip: {user_id} ({result['old_value']})")
            else:
                migrated += 1
                action_word = "Would migrate" if dry_run else "Migrated"
                print_success(
                    f"  {action_word}: {user_id} "
                    f"({result['old_value']} -> {result['new_value']})"
                )
    
    # Summary
    print()
    print(f"{Colors.BOLD}Summary{Colors.RESET}")
    print("=" * 50)
    print(f"Total users:  {total_users}")
    print(f"Migrated:     {migrated}")
    print(f"Skipped:      {skipped} (already have role)")
    print(f"Errors:       {errors}")
    
    if dry_run and migrated > 0:
        print()
        print_warning("This was a dry run. No changes were made.")
        print_info("Run with --apply to apply changes.")
    elif not dry_run and migrated > 0:
        print()
        print_success(f"Successfully migrated {migrated} users!")
    elif migrated == 0 and errors == 0:
        print()
        print_success("All users already migrated or no users to migrate.")
    
    return errors == 0


def main():
    parser = argparse.ArgumentParser(
        description="Migrate user roles from isAdmin to role field"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying (default behavior)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the migration (required to make changes)"
    )
    parser.add_argument(
        "--org-id",
        type=str,
        help="Migrate only a specific organization"
    )
    parser.add_argument(
        "--cred-path",
        type=str,
        help="Path to Firebase service account JSON file"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="Firebase Realtime Database URL"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show skipped users as well"
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither specified
    dry_run = not args.apply
    
    if args.apply and args.dry_run:
        print_error("Cannot specify both --apply and --dry-run")
        sys.exit(1)
    
    # Initialize Firebase
    init_firebase(args.cred_path, args.database_url)
    
    # Run migration
    success = run_migration(
        dry_run=dry_run,
        org_id=args.org_id,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
