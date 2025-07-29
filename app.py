#!/usr/bin/env python3
"""
GreenPulse - Render Deployment Entry Point
Optimized for Render auto-deployment
"""
import os
import sys
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def wait_for_database():
    """Wait for database connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️ No DATABASE_URL - running without database")
        return True
        
    from sqlalchemy import create_engine, text
    
    for attempt in range(20):
        try:
            print(f"🔍 Connecting to database... ({attempt + 1}/20)")
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connected!")
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            time.sleep(2)
    
    print("🚨 Database connection failed - continuing anyway")
    return False

def create_demo_data():
    """Create demo data if database is empty"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return
            
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data exists
        count = session.execute(text("SELECT COUNT(*) FROM buildings")).scalar()
        if count > 0:
            print(f"✅ Found {count} buildings - demo data ready")
            return
        
        print("🔧 Creating demo data...")
        
        # Create buildings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS buildings (
                id SERIAL PRIMARY KEY,
                site_id INTEGER DEFAULT 0,
                name VARCHAR(255) NOT NULL,
                building_type VARCHAR(100),
                primary_use VARCHAR(100),
                area_sqft INTEGER,
                year_built INTEGER,
                floor_count INTEGER,
                current_usage DECIMAL(10, 2) DEFAULT 100.0,
                efficiency_score INTEGER DEFAULT 80
            )
        """))
        
        # Create energy readings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS energy_readings (
                id SERIAL PRIMARY KEY,
                building_id INTEGER,
                site_id INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                meter_reading DECIMAL(10, 2) NOT NULL,
                meter_type INTEGER DEFAULT 0,
                air_temperature DECIMAL(5, 2) DEFAULT 22.0,
                cost_usd DECIMAL(8, 2) DEFAULT 10.0,
                carbon_emissions_lbs DECIMAL(8, 2) DEFAULT 50.0,
                efficiency_score INTEGER DEFAULT 80
            )
        """))
        
        # Insert demo buildings
        buildings_data = [
            ('Academic Building 1', 'academic', 'Education', 15000, 2010),
            ('Library Complex', 'academic', 'Library', 12000, 2005),
            ('Student Center', 'entertainment', 'Recreation', 20000, 2015),
            ('Office Building A', 'office', 'Office', 18000, 2008),
            ('Research Lab', 'academic', 'Laboratory', 10000, 2018),
            ('Dormitory East', 'residential', 'Housing', 25000, 2012),
            ('Dining Hall', 'retail', 'Food', 8000, 2009),
            ('Gymnasium', 'entertainment', 'Sports', 15000, 2000),
            ('Science Building', 'academic', 'Education', 22000, 2016),
            ('Administration', 'office', 'Administrative', 12000, 2003)
        ]
        
        for i, (name, btype, use, area, year) in enumerate(buildings_data, 1):
            session.execute(text("""
                INSERT INTO buildings (id, name, building_type, primary_use, area_sqft, year_built, floor_count, current_usage, efficiency_score)
                VALUES (:id, :name, :type, :use, :area, :year, :floors, :usage, :score)
            """), {
                'id': i, 'name': name, 'type': btype, 'use': use, 'area': area, 
                'year': year, 'floors': i + 1, 'usage': 80 + i * 5, 'score': 70 + i * 2
            })
        
        # Create sample energy readings
        from datetime import datetime, timedelta
        import random
        
        start_time = datetime.now() - timedelta(days=1)
        
        for building_id in range(1, 11):
            for hour in range(24):
                timestamp = start_time + timedelta(hours=hour)
                reading = 50 + random.uniform(20, 100) + building_id * 5
                
                session.execute(text("""
                    INSERT INTO energy_readings (building_id, timestamp, meter_reading, cost_usd, carbon_emissions_lbs)
                    VALUES (:bid, :ts, :reading, :cost, :carbon)
                """), {
                    'bid': building_id,
                    'ts': timestamp,
                    'reading': reading,
                    'cost': reading * 0.12,
                    'carbon': reading * 0.9
                })
        
        session.commit()
        session.close()
        print("✅ Demo data created successfully!")
        
    except Exception as e:
        print(f"⚠️ Demo data creation failed: {e}")

# Import FastAPI app
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting GreenPulse on port {port}")
    
    # Setup database
    if wait_for_database():
        create_demo_data()
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")