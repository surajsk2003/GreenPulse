#!/bin/bash

# 🚀 Super Easy GreenPulse Deployment Script
# Deploys to Render (backend) + Vercel (frontend) - completely FREE!

echo "🌟 GreenPulse Easy Deployment"
echo "============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if git repo is up to date
print_step "Checking git status..."
if ! git diff --quiet; then
    print_warning "You have uncommitted changes. Committing them now..."
    git add -A
    git commit -m "Auto-commit before deployment $(date)"
fi

if ! git diff --quiet HEAD origin/main; then
    print_warning "Local changes not pushed. Pushing to GitHub..."
    git push origin main
fi

print_success "Git repository is up to date"

# Update frontend environment for production
print_step "Updating frontend environment..."
cd frontend/greenpulse-dashboard

# Create production environment file
cat > src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: 'https://greenpulse-backend.onrender.com/api'
};
EOF

print_success "Frontend environment updated"

# Build frontend locally to check for errors
print_step "Testing frontend build..."
if npm run build > /dev/null 2>&1; then
    print_success "Frontend builds successfully"
else
    print_error "Frontend build failed. Please fix errors first."
    exit 1
fi

cd ../..

# Commit the environment changes
git add frontend/greenpulse-dashboard/src/environments/environment.prod.ts
git commit -m "Update production environment for deployment" || true
git push origin main

print_success "All preparation completed!"

echo ""
echo "🎯 DEPLOYMENT INSTRUCTIONS"
echo "========================="
echo ""

echo -e "${BLUE}1. RENDER BACKEND DEPLOYMENT (FREE):${NC}"
echo "   • Go to: https://render.com"
echo "   • Click 'Get Started for Free'"
echo "   • Connect your GitHub account"
echo "   • Click 'New +' → 'Web Service'"
echo "   • Connect your GreenPulse repository"
echo "   • Settings:"
echo "     - Name: greenpulse-backend"
echo "     - Environment: Python 3"
echo "     - Build Command: pip install -r requirements.txt"
echo "     - Start Command: python application.py"
echo "     - Plan: Free"
echo "   • Click 'Create Web Service'"
echo "   • Also create a PostgreSQL database (Free plan)"
echo ""

echo -e "${BLUE}2. VERCEL FRONTEND DEPLOYMENT (FREE):${NC}"
echo "   • Go to: https://vercel.com"
echo "   • Click 'Start Deploying'"
echo "   • Import your GreenPulse repository"
echo "   • Settings:"
echo "     - Framework Preset: Angular"
echo "     - Root Directory: frontend/greenpulse-dashboard"
echo "     - Build Command: npm run build"
echo "     - Output Directory: dist/greenpulse-dashboard"
echo "   • Click 'Deploy'"
echo ""

echo -e "${BLUE}3. ALTERNATIVE - NETLIFY FRONTEND (FREE):${NC}"
echo "   • Go to: https://netlify.com"
echo "   • Drag and drop: frontend/greenpulse-dashboard/dist/greenpulse-dashboard"
echo "   • Or connect GitHub repo with same settings as Vercel"
echo ""

echo -e "${GREEN}🎉 EXPECTED RESULTS:${NC}"
echo "   • Backend: https://greenpulse-backend.onrender.com"
echo "   • Frontend: https://greenpulse-frontend.vercel.app (or .netlify.app)"
echo "   • Database: Automatically connected PostgreSQL"
echo "   • Demo Data: Created automatically on first startup"
echo ""

echo -e "${YELLOW}📱 DEMO READY FEATURES:${NC}"
echo "   ✅ Modern glassmorphism dark UI"
echo "   ✅ Real-time WebSocket updates"
echo "   ✅ ML-powered energy analytics"
echo "   ✅ Interactive charts and insights"
echo "   ✅ 10 demo buildings with realistic data"
echo "   ✅ Mobile-responsive design"
echo ""

echo -e "${BLUE}🔗 USEFUL LINKS:${NC}"
echo "   • Render Dashboard: https://dashboard.render.com"
echo "   • Vercel Dashboard: https://vercel.com/dashboard"
echo "   • GitHub Repo: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git/\1/')"
echo ""

print_success "Deployment preparation completed! Follow the instructions above."

# Optional: Open the deployment sites
read -p "🌐 Open deployment sites in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://render.com"
    sleep 2
    open "https://vercel.com"
fi

echo ""
echo -e "${GREEN}🏆 Your GreenPulse platform is ready for hackathon demo!${NC}"