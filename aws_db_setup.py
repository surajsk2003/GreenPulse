#!/usr/bin/env python3
"""
AWS RDS PostgreSQL setup script for GreenPulse
Creates database tables and populates with demo data
"""
import os
import sys
import boto3
from datetime import datetime, timedelta
import random
import math

def get_rds_connection_string():
    """Get RDS connection details from AWS environment or parameters"""
    # You'll need to set these after creating RDS instance
    rds_endpoint = os.getenv('RDS_ENDPOINT', 'your-rds-endpoint.amazonaws.com')
    rds_username = os.getenv('RDS_USERNAME', 'postgres')
    rds_password = os.getenv('RDS_PASSWORD', 'your-password')
    rds_database = os.getenv('RDS_DATABASE', 'greenpulse')
    
    return f"postgresql://{rds_username}:{rds_password}@{rds_endpoint}:5432/{rds_database}"

def create_tables():
    """Create database tables using SQLAlchemy"""
    try:
        from sqlalchemy import create_engine, text
        
        connection_string = get_rds_connection_string()
        engine = create_engine(connection_string)
        
        # Create tables
        with engine.connect() as conn:
            # Buildings table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS buildings (
                    id SERIAL PRIMARY KEY,
                    site_id INTEGER,
                    name VARCHAR(255) NOT NULL,
                    building_type VARCHAR(100),
                    primary_use VARCHAR(100),
                    area_sqft INTEGER,
                    year_built INTEGER,
                    floor_count INTEGER,
                    current_usage DECIMAL(10, 2),
                    efficiency_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Energy readings table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS energy_readings (
                    id SERIAL PRIMARY KEY,
                    building_id INTEGER REFERENCES buildings(id),
                    site_id INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    meter_reading DECIMAL(10, 2) NOT NULL,
                    meter_type INTEGER,
                    air_temperature DECIMAL(5, 2),
                    cloud_coverage DECIMAL(3, 1),
                    dew_temperature DECIMAL(5, 2),
                    precip_depth_1_hr DECIMAL(5, 2),
                    sea_level_pressure DECIMAL(7, 2),
                    wind_direction DECIMAL(5, 1),
                    wind_speed DECIMAL(5, 2),
                    year_built INTEGER,
                    floor_count INTEGER,
                    cost_usd DECIMAL(8, 2),
                    carbon_emissions_lbs DECIMAL(8, 2),
                    efficiency_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_energy_readings_building_timestamp 
                ON energy_readings(building_id, timestamp DESC)
            """))
            
            conn.commit()
            
        print("✅ Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def populate_demo_data():
    """Populate database with demo data"""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        connection_string = get_rds_connection_string()
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data already exists
        existing = session.execute(text("SELECT COUNT(*) FROM buildings")).scalar()
        if existing > 0:
            print(f"✅ Found {existing} existing buildings, skipping demo data creation")
            return True
        
        print("🏢 Creating demo buildings...")
        
        # Demo buildings data
        buildings = [
            {'name': 'Academic Building 1', 'building_type': 'academic', 'primary_use': 'Education', 'area_sqft': 15000, 'year_built': 2010},
            {'name': 'Library Complex', 'building_type': 'academic', 'primary_use': 'Library', 'area_sqft': 12000, 'year_built': 2005},
            {'name': 'Student Center', 'building_type': 'entertainment', 'primary_use': 'Entertainment/public assembly', 'area_sqft': 20000, 'year_built': 2015},
            {'name': 'Office Building A', 'building_type': 'office', 'primary_use': 'Office', 'area_sqft': 18000, 'year_built': 2008},
            {'name': 'Research Lab', 'building_type': 'academic', 'primary_use': 'Laboratory', 'area_sqft': 10000, 'year_built': 2018},
            {'name': 'Dormitory East', 'building_type': 'residential', 'primary_use': 'Lodging/residential', 'area_sqft': 25000, 'year_built': 2012},
            {'name': 'Dining Hall', 'building_type': 'retail', 'primary_use': 'Food sales', 'area_sqft': 8000, 'year_built': 2009},
            {'name': 'Gymnasium', 'building_type': 'entertainment', 'primary_use': 'Recreation', 'area_sqft': 15000, 'year_built': 2000},
            {'name': 'Science Building', 'building_type': 'academic', 'primary_use': 'Education', 'area_sqft': 22000, 'year_built': 2016},
            {'name': 'Administration', 'building_type': 'office', 'primary_use': 'Administrative', 'area_sqft': 12000, 'year_built': 2003}
        ]
        
        # Insert buildings
        for i, building in enumerate(buildings, 1):
            building_data = {
                'id': i,
                'site_id': 0,
                'name': building['name'],
                'building_type': building['building_type'],
                'primary_use': building['primary_use'],
                'area_sqft': building['area_sqft'],
                'year_built': building['year_built'],
                'floor_count': random.randint(2, 8),
                'current_usage': random.uniform(80, 200),
                'efficiency_score': random.randint(70, 95)
            }
            
            session.execute(text("""
                INSERT INTO buildings (id, site_id, name, building_type, primary_use, area_sqft, year_built, floor_count, current_usage, efficiency_score)
                VALUES (:id, :site_id, :name, :building_type, :primary_use, :area_sqft, :year_built, :floor_count, :current_usage, :efficiency_score)
            """), building_data)
        
        session.commit()
        print("✅ Demo buildings created")
        
        # Create sample energy data (last 3 days to keep it lightweight)
        print("⚡ Creating demo energy data...")
        
        start_time = datetime.now() - timedelta(days=3)
        current_time = start_time
        
        readings_batch = []
        while current_time <= datetime.now():
            for building_id in range(1, 11):
                # Generate realistic energy pattern
                hour = current_time.hour
                day_factor = 0.7 + 0.3 * abs((hour - 12) / 12)
                weekend_factor = 0.6 if current_time.weekday() >= 5 else 1.0
                
                base_consumption = random.uniform(50, 150)
                meter_reading = base_consumption * day_factor * weekend_factor * random.uniform(0.9, 1.1)
                
                reading = {
                    'building_id': building_id,
                    'site_id': 0,
                    'timestamp': current_time,
                    'meter_reading': round(meter_reading, 2),
                    'meter_type': random.choice([0, 1, 2, 3]),
                    'air_temperature': random.uniform(18, 32),
                    'cloud_coverage': random.uniform(0, 8),
                    'dew_temperature': random.uniform(10, 25),
                    'precip_depth_1_hr': random.uniform(0, 3),
                    'sea_level_pressure': random.uniform(1010, 1025),
                    'wind_direction': random.uniform(0, 360),
                    'wind_speed': random.uniform(0, 12),
                    'year_built': random.randint(2000, 2020),
                    'floor_count': random.randint(2, 8),
                    'cost_usd': round(meter_reading * 0.12, 2),
                    'carbon_emissions_lbs': round(meter_reading * 0.92, 1),
                    'efficiency_score': random.randint(70, 95)
                }
                readings_batch.append(reading)
            
            current_time += timedelta(hours=2)  # Every 2 hours to keep data manageable
        
        # Insert energy readings in batches
        batch_size = 500
        for i in range(0, len(readings_batch), batch_size):
            batch = readings_batch[i:i + batch_size]
            
            session.execute(text("""
                INSERT INTO energy_readings (
                    building_id, site_id, timestamp, meter_reading, meter_type,
                    air_temperature, cloud_coverage, dew_temperature, precip_depth_1_hr,
                    sea_level_pressure, wind_direction, wind_speed, year_built, floor_count,
                    cost_usd, carbon_emissions_lbs, efficiency_score
                ) VALUES (
                    :building_id, :site_id, :timestamp, :meter_reading, :meter_type,
                    :air_temperature, :cloud_coverage, :dew_temperature, :precip_depth_1_hr,
                    :sea_level_pressure, :wind_direction, :wind_speed, :year_built, :floor_count,
                    :cost_usd, :carbon_emissions_lbs, :efficiency_score
                )
            """), batch)
            
            session.commit()
            print(f"✅ Inserted batch {i//batch_size + 1}")
        
        session.close()
        print(f"✅ Created {len(readings_batch)} demo energy readings")
        return True
        
    except Exception as e:
        print(f"❌ Error populating demo data: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up AWS RDS PostgreSQL for GreenPulse...")
    
    if create_tables():
        if populate_demo_data():
            print("🎉 AWS database setup completed successfully!")
            return True
    
    print("❌ AWS database setup failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)