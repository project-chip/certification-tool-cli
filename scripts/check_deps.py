#!/usr/bin/env python3
"""Check for dependency conflicts and security issues."""
import subprocess
import sys


def run_safety_check():
    """Run safety check for known security vulnerabilities."""
    try:
        result = subprocess.run(["safety", "check", "--json"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("⚠️  Security vulnerabilities found:")
            print(result.stdout)
            return False
        else:
            print("✅ No known security vulnerabilities found")
            return True
    except FileNotFoundError:
        print("💡 Install 'safety' to check for security vulnerabilities: pip install safety")
        return True


def check_dependency_conflicts():
    """Check for dependency conflicts."""
    try:
        result = subprocess.run(["pip", "check"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print("⚠️  Dependency conflicts found:")
            print(result.stdout)
            return False
        else:
            print("✅ No dependency conflicts found")
            return True
    except FileNotFoundError:
        print("❌ pip not found")
        return False


def main():
    """Main function."""
    print("🔍 Checking dependencies...")

    safety_ok = run_safety_check()
    conflicts_ok = check_dependency_conflicts()

    if safety_ok and conflicts_ok:
        print("\n✅ All dependency checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some dependency checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
