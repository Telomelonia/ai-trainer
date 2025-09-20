#!/bin/bash
# CoreSense AI Platform - Production Deployment Script
# Automated deployment for various cloud platforms

set -e  # Exit on any error

echo "🚀 CoreSense AI Platform - Production Deployment"
echo "================================================"

# Configuration
APP_NAME="coresense-ai"
DOCKER_IMAGE="coresense:latest"
HEALTH_CHECK_URL="http://localhost:8501/_stcore/health"

# Functions
log_info() {
    echo "ℹ️  $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
    exit 1
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
    fi
    
    # Check if .env file exists
    if [ ! -f "../.env" ]; then
        log_error ".env file not found. Please create one from .env.example"
    fi
    
    # Check if required environment variables are set
    source ../.env
    if [ -z "$JWT_SECRET_KEY" ]; then
        log_error "JWT_SECRET_KEY not set in .env file"
    fi
    
    log_success "Requirements check passed"
}

build_docker_image() {
    log_info "Building Docker image..."
    
    cd ..
    docker build -f deployment/Dockerfile -t $DOCKER_IMAGE .
    cd deployment
    
    log_success "Docker image built successfully"
}

deploy_local() {
    log_info "Deploying locally with Docker Compose..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Health check
    if curl -f $HEALTH_CHECK_URL > /dev/null 2>&1; then
        log_success "Local deployment successful!"
        log_info "Application available at: http://localhost:8501"
    else
        log_error "Health check failed. Check logs with: docker-compose logs"
    fi
}

deploy_streamlit_cloud() {
    log_info "Preparing for Streamlit Cloud deployment..."
    
    # Check if git repo is clean
    cd ..
    if [ -n "$(git status --porcelain)" ]; then
        log_error "Git repository has uncommitted changes. Please commit first."
    fi
    
    # Push to main branch
    git push origin main
    
    log_success "Code pushed to GitHub"
    log_info "🌐 Now deploy manually on https://share.streamlit.io"
    log_info "📁 Main file: app/main_with_auth.py"
    log_info "🔐 Don't forget to add secrets in Streamlit Cloud dashboard"
}

deploy_railway() {
    log_info "Deploying to Railway..."
    
    # Check if railway CLI is installed
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not installed. Run: npm install -g @railway/cli"
    fi
    
    cd ..
    
    # Login to Railway (if not already)
    railway login
    
    # Deploy
    railway up
    
    log_success "Deployed to Railway!"
}

deploy_render() {
    log_info "Preparing for Render deployment..."
    
    # Create render.yaml if it doesn't exist
    if [ ! -f "../render.yaml" ]; then
        cat > ../render.yaml << EOF
services:
  - type: web
    name: coresense-ai
    env: docker
    dockerfilePath: ./deployment/Dockerfile
    envVars:
      - key: DATABASE_URL
        fromService:
          type: pserv
          name: coresense-db
          property: connectionString
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
databases:
  - name: coresense-db
    databaseName: coresense
    user: coresense
EOF
        log_info "Created render.yaml configuration"
    fi
    
    cd ..
    git add render.yaml
    git commit -m "Add Render configuration" || true
    git push origin main
    
    log_success "Ready for Render deployment!"
    log_info "🌐 Connect your GitHub repo at https://dashboard.render.com"
}

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  local       Deploy locally with Docker Compose"
    echo "  streamlit   Prepare for Streamlit Cloud deployment"
    echo "  railway     Deploy to Railway"
    echo "  render      Prepare for Render deployment"
    echo "  build       Build Docker image only"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local              # Deploy locally for testing"
    echo "  $0 streamlit          # Prepare for Streamlit Cloud"
    echo "  $0 railway            # Deploy to Railway"
}

# Main script
case "${1:-help}" in
    "local")
        check_requirements
        build_docker_image
        deploy_local
        ;;
    "streamlit")
        check_requirements
        deploy_streamlit_cloud
        ;;
    "railway")
        check_requirements
        deploy_railway
        ;;
    "render")
        check_requirements
        deploy_render
        ;;
    "build")
        check_requirements
        build_docker_image
        ;;
    "help"|*)
        show_help
        ;;
esac

echo ""
echo "🎉 Deployment process completed!"
echo "📚 Check the deployment documentation for next steps"