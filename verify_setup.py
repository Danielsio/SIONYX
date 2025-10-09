#!/usr/bin/env python3
"""
Setup Verification Script
Checks if SIONYX is properly configured and ready to run
"""

import sys
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)"

def check_file_exists(filepath, description):
    """Check if a file exists"""
    path = Path(filepath)
    return path.exists(), f"{description} ({'found' if path.exists() else 'missing'})"

def check_env_variables():
    """Check if .env has required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        return False, "No .env file found"
    
    required_vars = [
        'ORG_ID',
        'FIREBASE_API_KEY',
        'FIREBASE_DATABASE_URL',
        'FIREBASE_PROJECT_ID'
    ]
    
    # Load .env
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip()
    
    missing = [var for var in required_vars if var not in env_vars or not env_vars[var]]
    
    if missing:
        return False, f"Missing variables: {', '.join(missing)}"
    
    return True, f"All required variables present"

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'PyQt6',
        'requests',
        'cryptography',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    
    return True, "All dependencies installed"

def check_firebase_config():
    """Test Firebase configuration"""
    try:
        # Add src to path
        src_path = Path(__file__).parent / 'src'
        sys.path.insert(0, str(src_path))
        
        # Load .env
        from dotenv import load_dotenv
        load_dotenv()
        
        from utils.firebase_config import FirebaseConfig
        
        config = FirebaseConfig()
        return True, f"Firebase config valid (ORG_ID: {config.org_id})"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {e}"

def print_result(check_name, passed, message):
    """Print check result"""
    status = f"{Colors.GREEN}✓{Colors.ENDC}" if passed else f"{Colors.RED}✗{Colors.ENDC}"
    print(f"{status} {Colors.BOLD}{check_name:.<40}{Colors.ENDC} {message}")

def main():
    """Run all checks"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}SIONYX Setup Verification{Colors.ENDC}")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version()),
        ("requirements.txt", check_file_exists('requirements.txt', 'requirements.txt')),
        (".env file", check_file_exists('.env', '.env')),
        ("Environment Variables", check_env_variables()),
        ("Dependencies", check_dependencies()),
        ("Firebase Config", check_firebase_config()),
        ("Main Entry Point", check_file_exists('src/main.py', 'src/main.py')),
    ]
    
    all_passed = True
    for check_name, (passed, message) in checks:
        print_result(check_name, passed, message)
        if not passed:
            all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Ready to run SIONYX{Colors.ENDC}")
        print(f"\n{Colors.CYAN}To start the application:{Colors.ENDC}")
        print(f"  python src/main.py")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some checks failed{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}To fix issues:{Colors.ENDC}")
        print(f"  1. Run: python install.py (to set up .env and organization)")
        print(f"  2. Run: pip install -r requirements.txt (to install dependencies)")
        print(f"  3. Check: env.example (for required environment variables)")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification cancelled{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
        sys.exit(1)


