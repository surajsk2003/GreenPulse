#!/bin/bash

echo "🚀 GreenPulse Railway Deployment Quick Test"
echo "=========================================="

# Get the Railway URLs (replace with your actual URLs)
BACKEND_URL="https://your-backend-service.up.railway.app"
FRONTEND_URL="https://your-frontend-service.up.railway.app"

echo "Testing Backend API..."
echo "1. Health Check:"
curl -s "$BACKEND_URL/health" | jq '.' 2>/dev/null || curl -s "$BACKEND_URL/health"

echo -e "\n2. Root Endpoint:"
curl -s "$BACKEND_URL/" | jq '.' 2>/dev/null || curl -s "$BACKEND_URL/"

echo -e "\n3. Buildings API:"
curl -s "$BACKEND_URL/api/buildings" | jq '.[0:2]' 2>/dev/null || curl -s "$BACKEND_URL/api/buildings"

echo -e "\n\nTesting Frontend..."
echo "Frontend Status:"
curl -I "$FRONTEND_URL" 2>/dev/null | head -n 1

echo -e "\n✅ If you see JSON responses above, your deployment is working!"
echo "🌐 Backend URL: $BACKEND_URL"
echo "🎨 Frontend URL: $FRONTEND_URL"