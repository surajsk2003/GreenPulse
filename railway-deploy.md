# 🚂 Railway Deployment Guide

## Step 1: Prepare for Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

## Step 2: Create railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "docker-config/Dockerfile.backend"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Step 3: Deploy Backend
```bash
# From project root
railway login
railway init
railway add --database postgresql
railway deploy

# Get your database URL
railway variables
```

## Step 4: Deploy Frontend (Separate Service)
```bash
# Create new Railway service for frontend
railway init frontend
railway deploy
```

## Step 5: Environment Variables
Set these in Railway dashboard:
- DATABASE_URL (auto-generated)
- CORS_ORIGINS=https://your-frontend-url.railway.app
- API_V1_STR=/api