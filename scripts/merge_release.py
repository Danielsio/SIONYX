#!/usr/bin/env python3
"""
Merge Release Branch to Main

Merges a release/* branch back to main after successful build/testing.
"""

import subprocess
import sys
from pathlib import Path
import json

# Force UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

VERSION_FILE = Path("sionyx-kiosk/version.json")


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


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"    {text}")
    print("=" * 60)
    print()


def main():
    print_header("Merge Release Branch to Main")
    
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")
    
    # Validate we're on a release branch
    if not current_branch.startswith("release/"):
        print(f"\n[ERROR] Not on a release branch.")
        print(f"Current branch: {current_branch}")
        print("Expected: release/x.y.z")
        sys.exit(1)
    
    # Check for uncommitted changes
    if has_uncommitted_changes():
        print("\n[ERROR] You have uncommitted changes.")
        print("Please commit or stash them before merging.")
        sys.exit(1)
    
    # Get version from branch name
    version = current_branch.replace("release/", "")
    print(f"Release version: v{version}")
    
    # Verify version matches version.json
    with open(VERSION_FILE) as f:
        version_data = json.load(f)
    
    if version_data["version"] != version:
        print(f"\n[ERROR] Version mismatch!")
        print(f"  Branch: {version}")
        print(f"  version.json: {version_data['version']}")
        sys.exit(1)
    
    print()
    
    # Checkout main and merge
    print("Switching to main...")
    result = run_cmd(["git", "checkout", "main"], check=False)
    if result.returncode != 0:
        print(f"[ERROR] Failed to checkout main: {result.stderr}")
        sys.exit(1)
    
    print("Pulling latest main...")
    run_cmd(["git", "pull", "origin", "main"], check=False)
    
    print(f"Merging {current_branch}...")
    result = run_cmd(["git", "merge", current_branch, "--no-ff", "-m", f"Release v{version}"], check=False)
    if result.returncode != 0:
        print(f"[ERROR] Merge failed: {result.stderr}")
        print("\nResolve conflicts and run: git merge --continue")
        sys.exit(1)
    
    # Create tag
    print(f"Creating tag v{version}...")
    run_cmd(["git", "tag", f"v{version}"], check=False)
    
    print()
    print("=" * 60)
    print(f"  ✅ Successfully merged release v{version} to main")
    print("=" * 60)
    print()
    print("Next steps:")
    print(f"  1. Push:   git push origin main --tags")
    print(f"  2. Delete: git branch -d {current_branch}")
    print()


if __name__ == "__main__":
    main()

