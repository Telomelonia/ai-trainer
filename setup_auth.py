#!/usr/bin/env python3
"""
CoreSense Authentication Setup Script
Automated setup for the authentication system
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("🚀 CoreSense Authentication System Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        
        # Install dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ pip not found. Please install pip first.")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        response = input("⚠️ .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("⏭️ Skipping .env file creation")
            return True
    
    if not env_example_path.exists():
        print("❌ .env.example file not found")
        return False
    
    try:
        # Read template
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        # Generate secure JWT secret
        jwt_secret = secrets.token_urlsafe(32)
        content = content.replace(
            "JWT_SECRET_KEY=your-super-secure-secret-key-change-in-production",
            f"JWT_SECRET_KEY={jwt_secret}"
        )
        
        # Get user input for basic configuration
        print("\n📝 Please provide basic configuration:")
        
        # Email configuration
        smtp_server = input("SMTP Server (default: smtp.gmail.com): ") or "smtp.gmail.com"
        smtp_port = input("SMTP Port (default: 587): ") or "587"
        smtp_username = input("SMTP Username (your email): ")
        smtp_password = input("SMTP Password (app password): ")
        from_email = input("From Email (default: noreply@coresense.ai): ") or "noreply@coresense.ai"
        
        # Application URL
        frontend_url = input("Frontend URL (default: http://localhost:8501): ") or "http://localhost:8501"
        
        # Update configuration
        replacements = {
            "SMTP_SERVER=smtp.gmail.com": f"SMTP_SERVER={smtp_server}",
            "SMTP_PORT=587": f"SMTP_PORT={smtp_port}",
            "SMTP_USERNAME=your-email@gmail.com": f"SMTP_USERNAME={smtp_username}",
            "SMTP_PASSWORD=your-app-password": f"SMTP_PASSWORD={smtp_password}",
            "FROM_EMAIL=noreply@coresense.ai": f"FROM_EMAIL={from_email}",
            "FRONTEND_URL=http://localhost:8501": f"FRONTEND_URL={frontend_url}"
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Write .env file
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ .env file created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def initialize_database():
    """Initialize the database"""
    print("\n🗄️ Initializing database...")
    
    try:
        # Add auth module to path
        auth_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth')
        sys.path.append(auth_path)
        
        # Import and initialize database
        from auth.database import db_service
        
        if db_service.initialize():
            print("✅ Database initialized successfully")
            return True
        else:
            print("❌ Failed to initialize database")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import auth modules: {e}")
        print("💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_admin_user():
    """Create an admin user"""
    print("\n👤 Creating admin user...")
    
    try:
        from auth.user_service import user_service, UserRegistrationData
        from auth.models import UserRole
        
        print("Please provide admin user details:")
        email = input("Admin Email: ")
        username = input("Admin Username: ")
        password = input("Admin Password: ")
        first_name = input("First Name: ")
        last_name = input("Last Name: ")
        
        # Create admin user
        registration_data = UserRegistrationData(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        result = user_service.register_user(registration_data)
        
        if result.success:
            # Upgrade to admin
            user_service.db_service.update_user(
                result.user.id,
                role=UserRole.ADMIN,
                is_verified=True
            )
            print("✅ Admin user created successfully")
            return True
        else:
            print(f"❌ Failed to create admin user: {result.message}")
            if result.errors:
                for error in result.errors:
                    print(f"   • {error}")
            return False
            
    except Exception as e:
        print(f"❌ Admin user creation failed: {e}")
        return False

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test authentication system import
        from auth import init_auth_system
        
        # Test initialization
        if init_auth_system():
            print("✅ Authentication system test passed")
            return True
        else:
            print("❌ Authentication system test failed")
            return False
            
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review and customize .env file if needed")
    print("2. Configure your email provider (Gmail app password, etc.)")
    print("3. Run the application:")
    print("   streamlit run app/main_with_auth.py")
    print()
    print("4. Open http://localhost:8501 in your browser")
    print("5. Test registration and login functionality")
    print()
    print("📚 Documentation:")
    print("   • Read AUTH_README.md for detailed documentation")
    print("   • Check .env.example for all configuration options")
    print()
    print("🔧 For production deployment:")
    print("   • Use PostgreSQL database")
    print("   • Enable HTTPS/SSL")
    print("   • Set proper CORS origins")
    print("   • Configure monitoring and logging")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Setup steps
    steps = [
        ("📦 Installing dependencies", install_dependencies),
        ("⚙️ Creating environment configuration", create_env_file),
        ("🗄️ Initializing database", initialize_database),
        ("🧪 Running tests", run_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            return False
    
    # Optional admin user creation
    print("\n" + "-" * 40)
    create_admin = input("Create admin user? (Y/n): ").lower()
    if create_admin != 'n':
        create_admin_user()
    
    print_next_steps()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)