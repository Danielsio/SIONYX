#!/usr/bin/env python3
"""
Test runner script for SIONYX
"""

import argparse
import subprocess
import sys


def run_tests(test_path=None, verbose=False, coverage=True, markers=None):
    """Run tests with specified options"""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test path
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])

    # Add markers
    if markers:
        cmd.extend(["-m", markers])

    # Add other options
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("❌ Tests failed!")
        return e.returncode


def run_linting():
    """Run code linting"""
    print("Running code linting...")
    print("-" * 30)

    lint_commands = [
        ["python", "-m", "black", "--check", "src/", "tests/"],
        ["python", "-m", "isort", "--check-only", "src/", "tests/"],
        ["python", "-m", "flake8", "src/", "tests/"],
        ["python", "-m", "mypy", "src/"],
    ]

    for cmd in lint_commands:
        print(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Passed")
        except subprocess.CalledProcessError:
            print("❌ Failed")
            return False

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SIONYX Test Runner")
    parser.add_argument("--path", "-p", help="Test path to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage")
    parser.add_argument("--markers", "-m", help="Pytest markers to filter tests")
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--all", action="store_true", help="Run tests and linting")

    args = parser.parse_args()

    if args.lint:
        success = run_linting()
        return 0 if success else 1

    if args.all:
        print("Running full test suite with linting...")
        print("=" * 50)

        # Run linting first
        if not run_linting():
            print("❌ Linting failed, stopping")
            return 1

        print("\n" + "=" * 50)
        print("Linting passed, running tests...")
        print("=" * 50)

    # Run tests
    return run_tests(
        test_path=args.path,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        markers=args.markers,
    )


if __name__ == "__main__":
    sys.exit(main())
