#!/usr/bin/env python3
"""
Release Management Script

Full release flow in one command:
  1. Create release branch with version bump
  2. Build installer (runs tests with coverage check)
  3. Merge back to main
  4. Create git tag
  5. Push to remote

Usage:
    python scripts/release.py --minor   # 1.1.3 → 1.2.0
    python scripts/release.py --major   # 1.1.3 → 2.0.0
    python scripts/release.py --patch   # 1.1.3 → 1.1.4

Options:
    --dry-run       Preview what would happen
    --no-push       Don't push to remote (for local testing)
    --branch-only   Only create the branch (skip build/merge/push)
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


def run_cmd(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    else:
        return subprocess.run(cmd, check=check)


def run_cmd_live(cmd: list[str]) -> int:
    """Run a command with live output. Returns exit code."""
    result = subprocess.run(cmd)
    return result.returncode


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


def print_step(step: int, total: int, text: str):
    """Print a step indicator."""
    print()
    print(f"[{step}/{total}] {text}")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description="Create and complete a release")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="Major release (breaking changes)")
    group.add_argument("--minor", action="store_true", help="Minor release (new features)")
    group.add_argument("--patch", action="store_true", help="Patch release (bug fixes)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--no-push", action="store_true", help="Don't push to remote")
    parser.add_argument("--branch-only", action="store_true", help="Only create branch (skip build/merge)")
    
    args = parser.parse_args()
    
    # Determine bump type
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"
    
    total_steps = 2 if args.branch_only else 5
    if args.no_push:
        total_steps -= 1
    
    print_header(f"{bump_type.upper()} Release")
    
    # ─────────────────────────────────────────────────────────────────────
    # PRE-FLIGHT CHECKS
    # ─────────────────────────────────────────────────────────────────────
    
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")
    
    if current_branch != "main":
        print(f"\n[ERROR] Must be on main branch to create a release.")
        print(f"Current branch: {current_branch}")
        print(f"\nSwitch to main: git checkout main")
        sys.exit(1)
    
    if has_uncommitted_changes():
        print("\n[ERROR] You have uncommitted changes.")
        print("Please commit or stash them before creating a release.")
        sys.exit(1)
    
    # Pull latest
    print("Pulling latest main...")
    run_cmd(["git", "pull", "origin", "main"], check=False)
    
    # Load and bump version
    version_data = load_version()
    old_version = version_data["version"]
    new_data = bump_version(version_data.copy(), bump_type)
    new_version = new_data["version"]
    branch_name = f"release/{new_version}"
    
    print(f"\nVersion: v{old_version} → v{new_version}")
    print(f"Branch:  {branch_name}")
    
    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        print("\nWould execute:")
        print(f"  1. Create branch: {branch_name}")
        print(f"  2. Update version.json to {new_version}")
        if not args.branch_only:
            print(f"  3. Build installer")
            print(f"  4. Merge to main + tag v{new_version}")
            if not args.no_push:
                print(f"  5. Push to remote")
        return
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 1: Create release branch
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(1, total_steps, "Creating release branch")
    
    result = run_cmd(["git", "checkout", "-b", branch_name], check=False)
    if result.returncode != 0:
        if "already exists" in result.stderr:
            print(f"[ERROR] Branch {branch_name} already exists.")
            print(f"Delete it: git branch -D {branch_name}")
        else:
            print(f"[ERROR] Failed: {result.stderr}")
        sys.exit(1)
    
    print(f"✓ Created branch: {branch_name}")
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 2: Bump version
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(2, total_steps, "Updating version")
    
    save_version(new_data)
    run_cmd(["git", "add", str(VERSION_FILE)])
    run_cmd(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    
    print(f"✓ Version updated to {new_version}")
    
    if args.branch_only:
        print()
        print("=" * 60)
        print(f"  ✓ Release branch created: {branch_name}")
        print("=" * 60)
        print()
        print("Next steps (manual):")
        print(f"  1. Build:  cd sionyx-desktop && python build.py")
        print(f"  2. Test the installer")
        print(f"  3. Merge:  make merge-release")
        return
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: Build installer
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(3, total_steps, "Building installer")
    
    # Run build with live output
    exit_code = run_cmd_live(["python", "build.py"], )
    
    # Need to run from sionyx-desktop directory
    import os
    original_dir = os.getcwd()
    os.chdir("sionyx-desktop")
    
    exit_code = run_cmd_live(["python", "build.py"])
    
    os.chdir(original_dir)
    
    if exit_code != 0:
        print()
        print("[ERROR] Build failed!")
        print(f"You're still on branch: {branch_name}")
        print()
        print("Options:")
        print("  - Fix the issue and run: cd sionyx-desktop && python build.py")
        print(f"  - Abort release: git checkout main && git branch -D {branch_name}")
        sys.exit(1)
    
    print("✓ Build completed successfully")
    
    # Commit any build artifacts (version.json updates like build number, coverage)
    result = run_cmd(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("Committing build artifacts...")
        run_cmd(["git", "add", "-A"])
        run_cmd(["git", "commit", "-m", "chore: update build artifacts"])
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 4: Merge to main + tag
    # ─────────────────────────────────────────────────────────────────────
    
    step_num = 4 if not args.no_push else 4
    print_step(step_num, total_steps, "Merging to main")
    
    # Switch to main
    result = run_cmd(["git", "checkout", "main"], check=False)
    if result.returncode != 0:
        print(f"[ERROR] Failed to checkout main: {result.stderr}")
        sys.exit(1)
    
    # Merge release branch
    result = run_cmd(
        ["git", "merge", branch_name, "--no-ff", "-m", f"Release v{new_version}"],
        check=False
    )
    if result.returncode != 0:
        print(f"[ERROR] Merge failed: {result.stderr}")
        sys.exit(1)
    
    # Create tag (ignore if exists)
    run_cmd(["git", "tag", f"v{new_version}"], check=False)
    
    # Delete release branch
    run_cmd(["git", "branch", "-d", branch_name], check=False)
    
    print(f"✓ Merged to main")
    print(f"✓ Created tag: v{new_version}")
    print(f"✓ Deleted branch: {branch_name}")
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 5: Push
    # ─────────────────────────────────────────────────────────────────────
    
    if not args.no_push:
        print_step(5, total_steps, "Pushing to remote")
        
        result = run_cmd(["git", "push", "origin", "main", "--tags"], check=False)
        if result.returncode != 0:
            print(f"[WARN] Push failed: {result.stderr}")
            print("Push manually: git push origin main --tags")
        else:
            print("✓ Pushed to remote")
    
    # ─────────────────────────────────────────────────────────────────────
    # DONE
    # ─────────────────────────────────────────────────────────────────────
    
    print()
    print("=" * 60)
    print(f"  ✅ Release v{new_version} complete!")
    print("=" * 60)
    print()
    if args.no_push:
        print("Don't forget to push: git push origin main --tags")
        print()


if __name__ == "__main__":
    main()
