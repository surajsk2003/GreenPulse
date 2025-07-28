#!/bin/bash

# GreenPulse Setup Script
echo "🌱 GreenPulse: Smart Energy Management Platform"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Starting GreenPulse setup..."

# Build and start services
print_status "Building Docker containers..."
cd docker-config
docker-compose up -d --build

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 15

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_success "Docker containers are running!"
else
    print_error "Failed to start Docker containers"
    exit 1
fi

# Process ASHRAE data
print_status "Processing ASHRAE dataset..."
docker-compose exec backend python data-pipeline/ashrae_processor.py

if [ $? -eq 0 ]; then
    print_success "ASHRAE data processed successfully!"
else
    print_warning "Data processing encountered issues. The system may still work with limited data."
fi

# Show service URLs
echo ""
print_success "🎉 GreenPulse is now running!"
echo ""
echo "Access your services:"
echo "📊 Dashboard: http://localhost:4200"
echo "🔌 API Docs:  http://localhost:8000/docs"
echo "💾 Database:  localhost:5432 (postgres/password)"
echo ""
echo "To stop the services:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service_name]"
echo ""

# Optional: Open browser
read -p "Open dashboard in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open http://localhost:4200
    elif command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:4200
    else
        print_warning "Could not open browser automatically. Please visit http://localhost:4200"
    fi
fi

print_success "Setup completed! Happy energy monitoring! 🌱"