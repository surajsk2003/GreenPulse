# 🌊 DigitalOcean App Platform Deployment

## Step 1: Create .do/app.yaml
```yaml
name: greenpulse
services:
- name: backend
  source_dir: /
  github:
    repo: your-username/greenpulse
    branch: main
  run_command: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
  envs:
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
    value: ${db.DATABASE_URL}
  - key: CORS_ORIGINS
    scope: RUN_AND_BUILD_TIME
    value: ${APP_DOMAIN}

- name: frontend
  source_dir: /frontend/greenpulse-dashboard
  github:
    repo: your-username/greenpulse
    branch: main
  build_command: npm install && npm run build
  run_command: npx serve -s dist/greenpulse-dashboard -l $PORT
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 3000

databases:
- engine: PG
  name: db
  num_nodes: 1
  size: basic-xs
  version: "14"
```

## Deploy:
1. Push to GitHub
2. Create DigitalOcean App
3. Connect GitHub repo
4. Deploy automatically