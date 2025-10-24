#!/usr/bin/env python3
"""
SIONYX Linting Script
====================
Comprehensive linting for Python and JavaScript/React code
"""

import subprocess
import sys
from pathlib import Path
import argparse


def run_command(command, description, cwd=None):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"PASSED: {description}")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"FAILED: {description}")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False
            
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False


def lint_python():
    """Run Python linting tools"""
    print("\nPYTHON LINTING")
    print("="*60)
    
    success = True
    
    # Black - Code formatting
    success &= run_command(
        "black --check --diff src/ build.py",
        "Black - Code formatting check"
    )
    
    # isort - Import sorting
    success &= run_command(
        "isort --check-only --diff src/ build.py",
        "isort - Import sorting check"
    )
    
    # flake8 - Linting
    success &= run_command(
        "flake8 src/ build.py",
        "flake8 - Linting"
    )
    
    # mypy - Type checking
    success &= run_command(
        "mypy src/ build.py",
        "mypy - Type checking"
    )
    
    # pylint - Advanced linting
    success &= run_command(
        "pylint src/ build.py",
        "pylint - Advanced linting"
    )
    
    # bandit - Security linting
    success &= run_command(
        "bandit -r src/",
        "bandit - Security linting"
    )
    
    return success


def lint_javascript():
    """Run JavaScript/React linting tools"""
    print("\nJAVASCRIPT/REACT LINTING")
    print("="*60)
    
    web_dir = Path("sionyx-web")
    if not web_dir.exists():
        print("ERROR: sionyx-web directory not found")
        return False
    
    success = True
    
    # ESLint - Linting
    success &= run_command(
        "npm run lint",
        "ESLint - JavaScript/React linting",
        cwd=web_dir
    )
    
    # Prettier - Code formatting
    success &= run_command(
        "npm run format:check",
        "Prettier - Code formatting check",
        cwd=web_dir
    )
    
    return success


def fix_python():
    """Fix Python code formatting and imports"""
    print("\nFIXING PYTHON CODE")
    print("="*60)
    
    # Black - Format code
    run_command(
        "black src/ build.py",
        "Black - Formatting code"
    )
    
    # isort - Sort imports
    run_command(
        "isort src/ build.py",
        "isort - Sorting imports"
    )


def fix_javascript():
    """Fix JavaScript/React code formatting"""
    print("\nFIXING JAVASCRIPT/REACT CODE")
    print("="*60)
    
    web_dir = Path("sionyx-web")
    if not web_dir.exists():
        print("ERROR: sionyx-web directory not found")
        return False
    
    # ESLint --fix
    run_command(
        "npm run lint:fix",
        "ESLint - Fixing linting issues",
        cwd=web_dir
    )
    
    # Prettier - Format code
    run_command(
        "npm run format",
        "Prettier - Formatting code",
        cwd=web_dir
    )


def main():
    parser = argparse.ArgumentParser(description='SIONYX Linting Script')
    parser.add_argument('--python', action='store_true', help='Lint Python code only')
    parser.add_argument('--javascript', action='store_true', help='Lint JavaScript/React code only')
    parser.add_argument('--fix', action='store_true', help='Fix formatting issues')
    parser.add_argument('--install', action='store_true', help='Install linting dependencies')
    
    args = parser.parse_args()
    
    if args.install:
        print("Installing linting dependencies...")
        
        # Install Python dependencies
        run_command(
            "pip install -r requirements-dev.txt",
            "Installing Python linting dependencies"
        )
        
        # Install JavaScript dependencies
        web_dir = Path("sionyx-web")
        if web_dir.exists():
            run_command(
                "npm install",
                "Installing JavaScript linting dependencies",
                cwd=web_dir
            )
        
        print("\n✅ Dependencies installed successfully!")
        return
    
    if args.fix:
        if not args.javascript:
            fix_python()
        if not args.python:
            fix_javascript()
        print("\nSUCCESS: Code formatting completed!")
        return
    
    # Run linting
    success = True
    
    if args.python or not (args.python or args.javascript):
        success &= lint_python()
    
    if args.javascript or not (args.python or args.javascript):
        success &= lint_javascript()
    
    if success:
        print("\nSUCCESS: All linting checks passed!")
        sys.exit(0)
    else:
        print("\nFAILED: Some linting checks failed!")
        print("Run with --fix to automatically fix formatting issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
