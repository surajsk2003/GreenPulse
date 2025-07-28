# 🔗 Ngrok Demo Setup (Perfect for Hackathons!)

## Why Ngrok for Hackathons?
- ✅ Runs on your laptop (no deployment issues)
- ✅ Instant public URL
- ✅ Perfect for live demos
- ✅ Works with your existing setup

## Step 1: Install Ngrok
```bash
# Install ngrok
brew install ngrok  # Mac
# or download from https://ngrok.com/download

# Sign up and get auth token
ngrok config add-authtoken YOUR_TOKEN
```

## Step 2: Expose Your Services
```bash
# Terminal 1: Start your Docker services
cd /Users/surajkumar/Desktop/GreenPulse/docker-config
docker-compose up

# Terminal 2: Expose frontend (4200)
ngrok http 4200 --domain=your-custom-domain.ngrok.app

# Terminal 3: Expose backend (8000) 
ngrok http 8000 --domain=your-api-domain.ngrok.app
```

## Step 3: Update Frontend API URL
Update your Angular environment:
```typescript
// src/environments/environment.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-api-domain.ngrok.app/api'
};
```

## Demo Day Setup:
1. Start Docker: `docker-compose up`
2. Start Ngrok: `ngrok http 4200`
3. Share URL: `https://your-domain.ngrok.app`
4. Judges can access from anywhere!

## Pro Tips:
- Get a custom ngrok domain (looks professional)
- Test the public URL before demo
- Have backup: laptop screen sharing
- Keep Docker logs visible for troubleshooting