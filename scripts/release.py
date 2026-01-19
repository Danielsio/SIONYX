#!/usr/bin/env python3
"""
Release Management Script (Atomic)

Full release flow in one command with atomic guarantees:
  - Version is only bumped AFTER successful build
  - On failure, everything is rolled back

Flow:
  1. Create release branch
  2. Build installer (tests must pass)
  3. If build succeeds → bump version, commit, merge, tag, push
  4. If build fails → delete branch, no version change

Usage:
    python scripts/release.py --minor   # 1.1.3 → 1.2.0
    python scripts/release.py --major   # 1.1.3 → 2.0.0
    python scripts/release.py --patch   # 1.1.3 → 1.1.4

Options:
    --dry-run       Preview what would happen
    --no-push       Don't push to remote (for local testing)
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
    data["buildNumber"] = data.get("buildNumber", 0) + 1
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


def abort_release(branch_name: str, reason: str):
    """Abort release and clean up."""
    print()
    print(f"[ABORT] {reason}")
    print()
    
    # Switch back to main
    run_cmd(["git", "checkout", "main"], check=False)
    
    # Delete the release branch
    run_cmd(["git", "branch", "-D", branch_name], check=False)
    
    print(f"✓ Cleaned up branch: {branch_name}")
    print("No version changes were made.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Create and complete a release (atomic)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--major", action="store_true", help="Major release (breaking changes)")
    group.add_argument("--minor", action="store_true", help="Minor release (new features)")
    group.add_argument("--patch", action="store_true", help="Patch release (bug fixes)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--no-push", action="store_true", help="Don't push to remote")
    parser.add_argument("--skip-coverage-check", action="store_true", help="Skip coverage check (for critical fixes)")
    
    args = parser.parse_args()
    
    # Determine bump type
    if args.major:
        bump_type = "major"
    elif args.minor:
        bump_type = "minor"
    else:
        bump_type = "patch"
    
    total_steps = 5 if not args.no_push else 4
    
    print_header(f"ATOMIC {bump_type.upper()} Release")
    
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
    
    # Calculate new version (but don't save yet!)
    version_data = load_version()
    old_version = version_data["version"]
    new_data = bump_version(version_data.copy(), bump_type)
    new_version = new_data["version"]
    branch_name = f"release/{new_version}"
    
    print(f"\nVersion: v{old_version} → v{new_version}")
    print(f"Branch:  {branch_name}")
    print()
    print("⚠️  ATOMIC: Version will only be bumped after successful build")
    
    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        print("\nWould execute:")
        print(f"  1. Create branch: {branch_name}")
        print(f"  2. Build installer with version {new_version}")
        print(f"  3. If build succeeds → bump version.json, commit")
        print(f"  4. Merge to main + tag v{new_version}")
        if not args.no_push:
            print(f"  5. Push to remote (main, tag, release branch)")
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
    # STEP 2: Build installer (with new version, but don't commit yet)
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(2, total_steps, f"Building installer v{new_version}")
    
    # Run build from sionyx-desktop directory
    # Use --version to set specific version without auto-bump
    import os
    original_dir = os.getcwd()
    os.chdir("sionyx-desktop")
    
    # Build with specific version - this will update version.json if successful
    build_cmd = ["python", "build.py", "--version", new_version]
    if args.skip_coverage_check:
        build_cmd.append("--skip-coverage-check")
    exit_code = run_cmd_live(build_cmd)
    
    os.chdir(original_dir)
    
    if exit_code != 0:
        os.chdir(original_dir)  # Make sure we're back
        abort_release(branch_name, "Build failed! Rolling back...")
    
    print("✓ Build completed successfully")
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: Commit the version bump (only after successful build)
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(3, total_steps, "Committing version bump")
    
    # Commit all changes (version.json was updated by build.py)
    run_cmd(["git", "add", "-A"])
    run_cmd(["git", "commit", "-m", f"release: v{new_version}"])
    
    print(f"✓ Committed release v{new_version}")
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 4: Merge to main + tag
    # ─────────────────────────────────────────────────────────────────────
    
    print_step(4, total_steps, "Merging to main + creating tag")
    
    # Switch to main
    result = run_cmd(["git", "checkout", "main"], check=False)
    if result.returncode != 0:
        print(f"[ERROR] Failed to checkout main: {result.stderr}")
        sys.exit(1)
    
    # Merge release branch
    result = run_cmd(
        ["git", "merge", branch_name, "--no-ff", "-m", f"Merge release v{new_version}"],
        check=False
    )
    if result.returncode != 0:
        print(f"[ERROR] Merge failed: {result.stderr}")
        sys.exit(1)
    
    # Create tag
    run_cmd(["git", "tag", f"v{new_version}"], check=False)
    
    print(f"✓ Merged to main")
    print(f"✓ Created tag: v{new_version}")
    
    # ─────────────────────────────────────────────────────────────────────
    # STEP 5: Push (main, tag, and release branch)
    # ─────────────────────────────────────────────────────────────────────
    
    if not args.no_push:
        print_step(5, total_steps, "Pushing to remote")
        
        # Push main branch with tags
        result = run_cmd(["git", "push", "origin", "main", "--tags"], check=False)
        if result.returncode != 0:
            print(f"[WARN] Push main failed: {result.stderr}")
            print("Push manually: git push origin main --tags")
        else:
            print("✓ Pushed main + tags")
        
        # Push release branch
        result = run_cmd(["git", "push", "origin", branch_name], check=False)
        if result.returncode != 0:
            print(f"[WARN] Push release branch failed: {result.stderr}")
            print(f"Push manually: git push origin {branch_name}")
        else:
            print(f"✓ Pushed release branch: {branch_name}")
    
    # ─────────────────────────────────────────────────────────────────────
    # DONE
    # ─────────────────────────────────────────────────────────────────────
    
    print()
    print("=" * 60)
    print(f"  ✅ Release v{new_version} complete!")
    print("=" * 60)
    print()
    print(f"  Tag:    v{new_version}")
    print(f"  Branch: {branch_name}")
    print()
    if args.no_push:
        print("Don't forget to push:")
        print(f"  git push origin main --tags")
        print(f"  git push origin {branch_name}")
        print()


if __name__ == "__main__":
    main()
