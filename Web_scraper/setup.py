#!/usr/bin/env python3
"""
Setup script for the e-commerce scraper.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"  ✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed: {e}")
        if e.stdout:
            print(f"    stdout: {e.stdout}")
        if e.stderr:
            print(f"    stderr: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_mongodb():
    """Check if MongoDB is accessible."""
    print("→ Checking MongoDB connection...")
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb+srv://user:pass@cluster.mongodb.net/", serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connection
        print("  ✓ MongoDB is accessible")
        client.close()
        return True
    except Exception as e:
        print(f"  ⚠ MongoDB not accessible: {e}")
        print("    Please ensure MongoDB is installed and running:")
        print("    brew install mongodb/brew/mongodb-community")
        print("    brew services start mongodb/brew/mongodb-community")
        return False

def install_dependencies():
    """Install Python dependencies."""
    requirements_file = "requirements.txt"
    if not Path(requirements_file).exists():
        print("✗ requirements.txt not found")
        return False
    
    return run_command(
        f"pip install -r {requirements_file}",
        "Installing Python dependencies"
    )

def setup_environment():
    """Setup environment variables."""
    env_example = Path(__file__).parent / ".env.example"
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if env_example.exists():
        print("→ Creating .env file from template...")
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("  ✓ .env file created")
            print("  ⚠ Please edit .env to configure your API keys")
            return True
        except Exception as e:
            print(f"  ✗ Failed to create .env file: {e}")
            return False
    else:
        print("⚠ .env.example not found, skipping environment setup")
        return True

def create_data_directory():
    """Create data directory for logs and output."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    print("✓ Data directory created")
    return True

def run_test():
    """Run the migration test."""
    test_script = Path(__file__).parent / "test_migration.py"
    if test_script.exists():
        print("\n" + "="*50)
        print("Running migration test...")
        print("="*50)
        return run_command(f"{sys.executable} {test_script} test", "Migration test")
    else:
        print("⚠ Test script not found, skipping test")
        return True

def main():
    """Main setup function."""
    print("E-commerce Scraper Setup")
    print("="*40)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check MongoDB
    mongodb_ok = check_mongodb()
    if not mongodb_ok:
        print("⚠ Continuing without MongoDB (some features may not work)")
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Setup environment
    if not setup_environment():
        success = False
    
    # Create data directory
    if not create_data_directory():
        success = False
    
    # Run test if everything else succeeded
    if success and mongodb_ok:
        if not run_test():
            success = False
    
    print("\n" + "="*50)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys (if needed)")
        print("2. Try the CLI: python cli.py 'rice'")
        print("3. Start the API: python app.py")
        print("4. Read README.md for full documentation")
    else:
        print("✗ Setup completed with some issues")
        print("Please check the errors above and retry")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
