#!/usr/bin/env python3
"""
Railway deployment startup script with database connection retry logic
"""
import os
import time
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
import uvicorn

def wait_for_database(max_retries=30, retry_interval=2):
    """Wait for database to be available with retry logic"""
    engine = None
    for attempt in range(max_retries):
        try:
            print(f"🔍 Attempt {attempt + 1}/{max_retries}: Connecting to database...")
            engine = create_engine(settings.DATABASE_URL)
            
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("✅ Database connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print("🚨 Max database connection retries exceeded!")
                return False
        finally:
            if engine:
                engine.dispose()
    
    return False

def main():
    """Main startup function"""
    print("🚀 Starting GreenPulse Backend...")
    print(f"Database URL: {settings.DATABASE_URL[:50]}...")
    print(f"Port: {settings.PORT}")
    
    # Wait for database to be ready
    if not wait_for_database():
        print("💥 Failed to connect to database. Exiting...")
        sys.exit(1)
    
    # Initialize demo data if needed
    try:
        print("🔧 Running Railway initialization...")
        from railway_init import main as init_main
        if init_main():
            print("✅ Railway initialization completed")
        else:
            print("⚠️ Railway initialization failed, continuing anyway...")
    except Exception as e:
        print(f"⚠️ Railway initialization error: {e}")
        print("Continuing with server startup...")
    
    # Start the FastAPI server
    print("🌱 Starting FastAPI server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()