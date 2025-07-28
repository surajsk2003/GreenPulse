# ⚡ QUICK DEPLOYMENT FOR HACKATHON

## Option 1: Ngrok (Recommended - 5 minutes)
```bash
# 1. Install ngrok
brew install ngrok

# 2. Get free account at ngrok.com, copy auth token
ngrok config add-authtoken YOUR_TOKEN_HERE

# 3. Start your system
cd /Users/surajkumar/Desktop/GreenPulse/docker-config
docker-compose up -d

# 4. Create public tunnel
ngrok http 4200

# 5. Share the https://xxxxx.ngrok.app URL with judges!
```

## Option 2: Railway (15 minutes)
```bash
# 1. Push code to GitHub first
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to railway.app, connect GitHub
# 3. Deploy backend + database
# 4. Deploy frontend separately
# 5. Get production URLs
```

## Option 3: Emergency Backup
- Use your laptop for demo
- Share screen via Zoom/Teams
- Have ngrok ready as backup
- Keep Docker running locally

## Demo Day Checklist:
- [ ] Test public URL works
- [ ] Check WebSocket connections
- [ ] Verify database data loads
- [ ] Test on mobile device
- [ ] Have backup plan ready
- [ ] Screenshot key features