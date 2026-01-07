#!/usr/bin/env python3
"""
Release Management Script

Creates a release branch with the bumped version.
Usage:
    python scripts/release.py --minor   # 1.1.3 → 1.2.0
    python scripts/release.py --major   # 1.1.3 → 2.0.0
    python scripts/release.py --patch   # 1.1.3 → 1.1.4
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

VERSION_FILE = Path("sionyx-desktop/version.json")


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_current_branch() -> str:
    """Get the current git branch name."""
    result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes."""
    result = run_cmd(["git", "status", "--porcelain"])
    return bool(result.stdout.strip())


def load_version() -> dict:
    """Load version.json."""
    with open(VERSION_FILE) as f:
        return json.load(f)


def save_version(data: dict):
    """Save version.json."""
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=2)


def bump_version(data: dict, bump_type: str) -> dict:
    """Bump the version according to type."""
    major = data["major"]
    minor = data["minor"]
    patch = data["patch"]
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    
    data["major"] = major
    data["minor"] = minor
    data["patch"] = patch
    data["version"] = f"{major}.{minor}.{patch}"
    data["lastBuildDate"] = datetime.now().isoformat()
    
    return data


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"    {text}")
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(description="Create a release branch")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="Major release (breaking changes)")
    group.add_argument("--minor", action="store_true", help="Minor release (new features)")
    group.add_argument("--patch", action="store_true", help="Patch release (bug fixes)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    
    args = parser.parse_args()
    
    # Determine bump type
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"
    
    print_header(f"Creating {bump_type.upper()} Release")
    
    # Check current branch
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")
    
    if current_branch != "main":
        print(f"\n[WARN] Not on main branch. Currently on: {current_branch}")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(1)
    
    # Check for uncommitted changes
    if has_uncommitted_changes():
        print("\n[ERROR] You have uncommitted changes.")
        print("Please commit or stash them before creating a release.")
        sys.exit(1)
    
    # Load current version
    version_data = load_version()
    old_version = version_data["version"]
    print(f"Current version: v{old_version}")
    
    # Calculate new version
    new_data = bump_version(version_data.copy(), bump_type)
    new_version = new_data["version"]
    branch_name = f"release/{new_version}"
    
    print(f"New version:     v{new_version}")
    print(f"Release branch:  {branch_name}")
    
    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return
    
    print()
    
    # Create and checkout release branch
    print(f"Creating branch: {branch_name}")
    result = run_cmd(["git", "checkout", "-b", branch_name], check=False)
    if result.returncode != 0:
        if "already exists" in result.stderr:
            print(f"[ERROR] Branch {branch_name} already exists.")
            print(f"  Delete it with: git branch -D {branch_name}")
        else:
            print(f"[ERROR] Failed to create branch: {result.stderr}")
        sys.exit(1)
    
    # Update version.json
    print("Updating version.json...")
    save_version(new_data)
    
    # Commit the version bump
    print("Committing version bump...")
    run_cmd(["git", "add", str(VERSION_FILE)])
    run_cmd(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    
    print()
    print("=" * 60)
    print(f"  ✅ Release branch created: {branch_name}")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Build:     make build-{bump_type}")
    print(f"  2. Test the installer manually")
    print(f"  3. Merge:     make merge-release")
    print(f"  4. Tag:       git tag v{new_version}")
    print(f"  5. Push:      git push origin main --tags")
    print()


if __name__ == "__main__":
    main()

