# 🎨 Render Deployment Guide

## Step 1: Prepare render.yaml
```yaml
services:
  - type: web
    name: greenpulse-backend
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: greenpulse-db
          property: connectionString
      - key: CORS_ORIGINS
        value: https://greenpulse-frontend.onrender.com

  - type: web
    name: greenpulse-frontend
    env: static
    buildCommand: "cd frontend/greenpulse-dashboard && npm install && npm run build"
    staticPublishPath: frontend/greenpulse-dashboard/dist/greenpulse-dashboard
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

databases:
  - name: greenpulse-db
    databaseName: greenpulse
    user: postgres
```

## Steps:
1. Push code to GitHub
2. Connect Render to your GitHub repo
3. Render auto-deploys from render.yaml
4. Get URLs: 
   - Backend: https://greenpulse-backend.onrender.com
   - Frontend: https://greenpulse-frontend.onrender.com