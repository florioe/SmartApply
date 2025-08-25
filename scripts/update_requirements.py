#!/usr/bin/env python3
"""
Script to update requirements files using pip-tools.
This script helps maintain consistent dependency management.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main function to update requirements."""
    print("📦 SmartApply Dependency Management")
    print("=" * 50)
    
    # Check if pip-tools is installed
    try:
        subprocess.run(["pip-compile", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip-tools is not installed. Installing...")
        if not run_command("pip install pip-tools", "Installing pip-tools"):
            print("Failed to install pip-tools. Please install manually:")
            print("pip install pip-tools")
            return False
    
    # Update base requirements
    success = True
    success &= run_command(
        "pip-compile requirements/base.in --output-file=requirements/base.txt",
        "Updating base requirements"
    )
    
    # The development.txt is manually maintained for now since it includes base.txt
    # but we could create a development.in if needed in the future
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All requirements updated successfully!")
        print("\n📋 Next steps:")
        print("1. Review the updated requirements files")
        print("2. Test your application with the new dependencies")
        print("3. Commit the changes to version control")
    else:
        print("❌ Some operations failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
