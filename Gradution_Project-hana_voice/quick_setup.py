#!/usr/bin/env python3
"""
Quick setup script for Finance Analyzer Enhanced Version
"""
import os
import sys
import subprocess
import asyncio

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("🔄 Creating .env file...")
        env_content = """# Finance Analyzer Configuration
ASSEMBLYAI_API_KEY=your_api_key_here
SECRET_KEY=your_secure_secret_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./finance_analyzer.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please update ASSEMBLYAI_API_KEY in .env file")
        return True
    else:
        print("✅ .env file already exists")
        return True

def main():
    """Main setup function"""
    print("🎯 Finance Analyzer Enhanced Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Create .env file
    if not create_env_file():
        return False
    
    # Setup database
    if not run_command("python setup_database.py", "Setting up database"):
        return False
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    print("✅ Models directory created")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update ASSEMBLYAI_API_KEY in .env file")
    print("2. Run: python main.py")
    print("3. Open: http://localhost:8000")
    print("4. View dashboard: http://localhost:8000/dashboard")
    print("\n💡 Optional: Train ML model with: python train_model.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)