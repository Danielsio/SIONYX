#!/usr/bin/env python3
"""
File formatter for sionyx-desktop.
Fixes line endings and trailing newlines for all Python files.
"""

import argparse
import sys
from pathlib import Path


def fix_file(filepath: Path, check_only: bool = False) -> bool:
    """
    Fix a single file:
    - Convert CRLF to LF
    - Ensure exactly one trailing newline

    Returns True if file was (or would be) modified.
    """
    try:
        content = filepath.read_bytes()
    except (IOError, OSError) as e:
        print(f"  Error reading {filepath}: {e}")
        return False

    original = content

    # Convert CRLF to LF
    content = content.replace(b"\r\n", b"\n")

    # Also handle standalone CR (old Mac style)
    content = content.replace(b"\r", b"\n")

    # Ensure exactly one trailing newline
    content = content.rstrip(b"\n") + b"\n"

    if content != original:
        if check_only:
            return True
        try:
            filepath.write_bytes(content)
            return True
        except (IOError, OSError) as e:
            print(f"  Error writing {filepath}: {e}")
            return False

    return False


def format_files(src_dir: Path, check_only: bool = False) -> tuple[int, int]:
    """
    Format all Python files in the given directory.

    Returns (total_files, modified_files) tuple.
    """
    extensions = {".py", ".pyi"}
    exclude_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "build",
        "dist",
        ".eggs",
        ".mypy_cache",
        ".pytest_cache",
        "htmlcov",
    }

    total = 0
    modified = 0

    for filepath in src_dir.rglob("*"):
        # Skip excluded directories
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue

        # Only process Python files
        if filepath.suffix not in extensions:
            continue

        if not filepath.is_file():
            continue

        total += 1
        if fix_file(filepath, check_only):
            modified += 1
            action = "would fix" if check_only else "fixed"
            print(f"  {action}: {filepath.relative_to(src_dir.parent)}")

    return total, modified


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fix line endings and trailing newlines for Python files"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, don't modify files (exit 1 if files need fixing)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="src",
        help="Directory to format (default: src)",
    )

    args = parser.parse_args()

    src_dir = Path(args.path)
    if not src_dir.exists():
        print(f"Error: Directory '{src_dir}' not found")
        return 1

    action = "Checking" if args.check else "Formatting"
    print(f"{action} Python files in {src_dir}/...")

    total, modified = format_files(src_dir, check_only=args.check)

    if args.check:
        if modified > 0:
            print(f"\n{modified}/{total} files need formatting")
            print("Run 'make format' to fix.")
            return 1
        else:
            print(f"\nAll {total} files OK!")
            return 0
    else:
        if modified > 0:
            print(f"\nFormatted {modified}/{total} files")
        else:
            print(f"\nAll {total} files already formatted")
        return 0


if __name__ == "__main__":
    sys.exit(main())
