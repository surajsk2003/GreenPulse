#!/usr/bin/env python3
"""
Universal application entry point for GreenPulse
Works with Render, AWS Elastic Beanstalk, and other platforms
"""
import os
import sys
import time
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment variables
os.environ.setdefault("PYTHONPATH", str(backend_dir))

def wait_for_database(max_retries=30, retry_interval=2):
    """Wait for database to be available with retry logic"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️ No DATABASE_URL found, skipping database check")
        return True
        
    engine = None
    for attempt in range(max_retries):
        try:
            print(f"🔍 Attempt {attempt + 1}/{max_retries}: Connecting to database...")
            engine = create_engine(database_url)
            
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

def initialize_demo_data():
    """Initialize demo data if needed"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("⚠️ No DATABASE_URL found, skipping demo data initialization")
            return True
            
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data already exists
        existing_buildings = session.execute(text("SELECT COUNT(*) FROM buildings")).scalar()
        if existing_buildings > 0:
            print(f"✅ Found {existing_buildings} existing buildings, skipping initialization")
            session.close()
            return True
        
        print("🔧 Initializing demo data...")
        
        # Use our existing railway_init script
        from railway_init import create_demo_buildings, create_demo_energy_data
        
        create_demo_buildings(session)
        create_demo_energy_data(session)
        
        session.close()
        print("✅ Demo data initialization completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Demo data initialization failed: {e}")
        print("Continuing without demo data...")
        return True

# Import the FastAPI app
from app.main import app

# For various deployment platforms
application = app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting GreenPulse - Port {port}")
    print(f"Platform: {os.environ.get('RENDER', 'Unknown')}")
    
    # Wait for database and initialize
    if wait_for_database():
        initialize_demo_data()
    
    # Start the server
    uvicorn.run(
        application,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )