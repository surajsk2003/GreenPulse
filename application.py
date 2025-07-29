#!/usr/bin/env python3
"""
AWS Elastic Beanstalk application entry point for GreenPulse
"""
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment variables for AWS
os.environ.setdefault("PYTHONPATH", str(backend_dir))

# Import the FastAPI app
from app.main import app

# For AWS Elastic Beanstalk
application = app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Elastic Beanstalk sets this)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting GreenPulse on AWS Elastic Beanstalk - Port {port}")
    
    uvicorn.run(
        application,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )