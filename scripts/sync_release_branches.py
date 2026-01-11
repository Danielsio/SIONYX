#!/usr/bin/env python3
"""
Sync Release Branches with Tags

Creates release branches for any tags that don't have corresponding branches.
This ensures every version tag (vX.Y.Z) has a matching release/X.Y.Z branch.

Usage:
    python scripts/sync_release_branches.py           # Sync all missing branches
    python scripts/sync_release_branches.py --dry-run # Preview what would happen
"""

import argparse
import subprocess
import sys


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def get_all_tags() -> list[str]:
    """Get all version tags sorted by version."""
    result = run_cmd(["git", "tag", "--sort=-v:refname"])
    tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
    # Filter to only version tags (vX.Y.Z format)
    return [t for t in tags if t.startswith("v") and t[1:2].isdigit()]


def get_all_release_branches() -> set[str]:
    """Get all release branches (local and remote)."""
    result = run_cmd(["git", "branch", "-a"])
    branches = set()
    for line in result.stdout.strip().split("\n"):
        line = line.strip().replace("* ", "")
        if "release/" in line:
            # Extract just the branch name without remotes/origin/
            if "remotes/origin/" in line:
                branch = line.replace("remotes/origin/", "")
            else:
                branch = line
            branches.add(branch)
    return branches


def main():
    parser = argparse.ArgumentParser(description="Sync release branches with tags")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    args = parser.parse_args()

    print("Syncing release branches with tags...")
    print()

    tags = get_all_tags()
    existing_branches = get_all_release_branches()

    print(f"Found {len(tags)} version tags")
    print(f"Found {len(existing_branches)} release branches")
    print()

    missing = []
    for tag in tags:
        version = tag[1:]  # Remove 'v' prefix
        branch_name = f"release/{version}"
        if branch_name not in existing_branches:
            missing.append((tag, branch_name))

    if not missing:
        print("✓ All tags have corresponding release branches!")
        return

    print(f"Missing {len(missing)} release branches:")
    for tag, branch in missing:
        print(f"  {tag} → {branch}")
    print()

    if args.dry_run:
        print("[DRY RUN] No changes made.")
        return

    # Create missing branches
    for tag, branch_name in missing:
        print(f"Creating {branch_name} from {tag}...")
        
        # Create local branch from tag
        result = run_cmd(["git", "branch", branch_name, tag], check=False)
        if result.returncode != 0:
            print(f"  [WARN] Failed to create branch: {result.stderr.strip()}")
            continue
        
        # Push to remote
        result = run_cmd(["git", "push", "origin", branch_name], check=False)
        if result.returncode != 0:
            print(f"  [WARN] Failed to push: {result.stderr.strip()}")
        else:
            print(f"  ✓ Created and pushed {branch_name}")

    print()
    print("✓ Sync complete!")


if __name__ == "__main__":
    main()
