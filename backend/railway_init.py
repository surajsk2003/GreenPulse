#!/usr/bin/env python3
"""
Railway initialization script for GreenPulse
Creates demo buildings and sample energy data for Railway deployment
"""
import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Add app to path
sys.path.append('/app')

def create_demo_buildings(session):
    """Create demo buildings with realistic data"""
    print("🏢 Creating demo buildings...")
    
    building_types = ['academic', 'office', 'residential', 'retail', 'entertainment']
    primary_uses = {
        'academic': ['Education', 'Laboratory', 'Library'],
        'office': ['Office', 'Administrative', 'Technology'],
        'residential': ['Lodging/residential', 'Student housing'],
        'retail': ['Retail', 'Food sales'],
        'entertainment': ['Entertainment/public assembly', 'Recreation']
    }
    
    buildings_data = []
    for i in range(10):  # Create 10 demo buildings
        building_type = random.choice(building_types)
        primary_use = random.choice(primary_uses[building_type])
        
        building = {
            'id': i + 1,
            'site_id': 0,
            'name': f'{building_type.title()} Building {i + 1}',
            'building_type': building_type,
            'primary_use': primary_use,
            'area_sqft': random.randint(5000, 50000),
            'year_built': random.randint(1990, 2020),
            'floor_count': random.randint(2, 15),
            'current_usage': random.uniform(80, 200),
            'efficiency_score': random.randint(60, 95)
        }
        buildings_data.append(building)
    
    # Insert buildings
    insert_query = text("""
        INSERT INTO buildings (id, site_id, name, building_type, primary_use, area_sqft, year_built, floor_count, current_usage, efficiency_score)
        VALUES (:id, :site_id, :name, :building_type, :primary_use, :area_sqft, :year_built, :floor_count, :current_usage, :efficiency_score)
        ON CONFLICT (id) DO NOTHING
    """)
    
    for building in buildings_data:
        try:
            session.execute(insert_query, building)
        except Exception as e:
            print(f"Error inserting building {building['id']}: {e}")
    
    session.commit()
    print(f"✅ Created {len(buildings_data)} demo buildings")

def create_demo_energy_data(session):
    """Create sample energy readings for the last 7 days"""
    print("⚡ Creating demo energy data...")
    
    # Get building IDs
    buildings = session.execute(text("SELECT id FROM buildings LIMIT 10")).fetchall()
    building_ids = [b[0] for b in buildings]
    
    if not building_ids:
        print("❌ No buildings found, skipping energy data creation")
        return
    
    # Generate data for last 7 days, every hour
    start_time = datetime.now() - timedelta(days=7)
    end_time = datetime.now()
    
    readings_data = []
    current_time = start_time
    
    while current_time <= end_time:
        for building_id in building_ids:
            # Generate realistic energy reading
            hour = current_time.hour
            day_factor = 0.7 + 0.3 * abs((hour - 12) / 12)  # Peak during midday
            
            # Weekend factor
            weekend_factor = 0.6 if current_time.weekday() >= 5 else 1.0
            
            # Base consumption
            base_consumption = random.uniform(50, 150)
            meter_reading = base_consumption * day_factor * weekend_factor * random.uniform(0.9, 1.1)
            
            reading = {
                'building_id': building_id,
                'site_id': 0,
                'timestamp': current_time,
                'meter_reading': round(meter_reading, 2),
                'meter_type': random.choice([0, 1, 2, 3]),  # electricity, chilledwater, steam, hotwater
                'air_temperature': random.uniform(15, 35),
                'cloud_coverage': random.uniform(0, 8),
                'dew_temperature': random.uniform(5, 25),
                'precip_depth_1_hr': random.uniform(0, 5),
                'sea_level_pressure': random.uniform(1010, 1025),
                'wind_direction': random.uniform(0, 360),
                'wind_speed': random.uniform(0, 15),
                'year_built': random.randint(1990, 2020),
                'floor_count': random.randint(2, 15),
                'cost_usd': round(meter_reading * 0.12, 2),  # $0.12 per kWh
                'carbon_emissions_lbs': round(meter_reading * 0.92, 1),  # 0.92 lbs CO2 per kWh
                'efficiency_score': random.randint(70, 95)
            }
            readings_data.append(reading)
        
        current_time += timedelta(hours=1)
    
    # Insert energy readings in batches
    batch_size = 1000
    insert_query = text("""
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
    """)
    
    for i in range(0, len(readings_data), batch_size):
        batch = readings_data[i:i + batch_size]
        try:
            session.execute(insert_query, batch)
            session.commit()
            print(f"✅ Inserted batch {i//batch_size + 1} ({len(batch)} readings)")
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            session.rollback()
    
    print(f"✅ Created {len(readings_data)} demo energy readings")

def main():
    """Initialize Railway deployment with demo data"""
    print("🚀 Initializing GreenPulse Railway deployment...")
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data already exists
        existing_buildings = session.execute(text("SELECT COUNT(*) FROM buildings")).scalar()
        if existing_buildings > 0:
            print(f"✅ Found {existing_buildings} existing buildings, skipping initialization")
            return True
        
        # Create demo data
        create_demo_buildings(session)
        create_demo_energy_data(session)
        
        session.close()
        print("🎉 Railway initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)