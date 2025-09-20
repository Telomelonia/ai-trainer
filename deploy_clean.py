"""
CoreSense AI Platform - Production Deployment Guide
Simplified deployment following best practices
"""

import os
import subprocess
import sys
from pathlib import Path
from core.config import get_config, validate_config
from core.logging import setup_logging, get_logger

logger = get_logger(__name__)


class DeploymentManager:
    """Simplified deployment manager"""
    
    def __init__(self):
        self.config = get_config()
        self.project_root = Path(__file__).parent.parent
    
    def validate_environment(self):
        """Validate deployment environment"""
        logger.info("🔍 Validating deployment environment...")
        
        try:
            validate_config()
            logger.info("✅ Configuration validation passed")
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False
        
        # Check required files
        required_files = [
            'requirements_clean.txt',
            '.env.clean',
            'app/main_clean.py'
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                logger.error(f"❌ Required file missing: {file_path}")
                return False
        
        logger.info("✅ Environment validation passed")
        return True
    
    def prepare_for_deployment(self):
        """Prepare application for deployment"""
        logger.info("🚀 Preparing for deployment...")
        
        # Copy clean configuration
        env_clean = self.project_root / '.env.clean'
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            logger.info("📋 Creating .env from clean template")
            env_file.write_text(env_clean.read_text())
        
        # Install clean requirements
        requirements_clean = self.project_root / 'requirements_clean.txt'
        if requirements_clean.exists():
            logger.info("📦 Installing clean requirements...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 
                str(requirements_clean)
            ], check=True)
        
        logger.info("✅ Deployment preparation completed")
    
    def run_local_server(self):
        """Run local development server"""
        logger.info("🖥️ Starting local development server...")
        
        main_file = self.project_root / 'app' / 'main_clean.py'
        
        subprocess.run([
            'streamlit', 'run', str(main_file),
            '--server.port', str(self.config.port),
            '--server.address', self.config.host
        ])
    
    def generate_streamlit_config(self):
        """Generate Streamlit configuration"""
        config_dir = self.project_root / '.streamlit'
        config_dir.mkdir(exist_ok=True)
        
        config_content = f"""
[server]
port = {self.config.port}
address = "{self.config.host}"
headless = true
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "{getattr(self.config, 'primary_color', '#6C63FF')}"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[logger]
level = "{self.config.log_level}"
"""
        
        config_file = config_dir / 'config.toml'
        config_file.write_text(config_content.strip())
        
        logger.info(f"✅ Streamlit config generated: {config_file}")
    
    def deploy_to_streamlit_cloud(self):
        """Prepare for Streamlit Cloud deployment"""
        logger.info("☁️ Preparing for Streamlit Cloud deployment...")
        
        # Generate necessary files
        self.generate_streamlit_config()
        
        # Check git status
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, check=True)
            if result.stdout.strip():
                logger.warning("⚠️ Git repository has uncommitted changes")
                logger.info("Please commit changes before deployment")
            else:
                logger.info("✅ Git repository is clean")
        except subprocess.CalledProcessError:
            logger.warning("⚠️ Git not available or not a git repository")
        
        logger.info("📋 Streamlit Cloud deployment instructions:")
        logger.info("1. Push code to GitHub")
        logger.info("2. Go to https://share.streamlit.io")
        logger.info("3. Select your repository")
        logger.info("4. Set main file: app/main_clean.py")
        logger.info("5. Add secrets from .env.clean")


def main():
    """Main deployment script"""
    setup_logging(level="INFO")
    
    if len(sys.argv) < 2:
        print("Usage: python deploy_clean.py [validate|prepare|local|streamlit]")
        sys.exit(1)
    
    command = sys.argv[1]
    deployer = DeploymentManager()
    
    if command == "validate":
        success = deployer.validate_environment()
        sys.exit(0 if success else 1)
    
    elif command == "prepare":
        deployer.prepare_for_deployment()
    
    elif command == "local":
        deployer.validate_environment()
        deployer.prepare_for_deployment()
        deployer.run_local_server()
    
    elif command == "streamlit":
        deployer.validate_environment()
        deployer.prepare_for_deployment()
        deployer.deploy_to_streamlit_cloud()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()