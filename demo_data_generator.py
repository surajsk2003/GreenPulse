#!/usr/bin/env python3
"""
Quick demo data generator for hackathon presentation
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.core.database import SessionLocal
from backend.app.models.database import Building, EnergyReading, Anomaly, Insight

def generate_demo_data():
    """Generate realistic demo data quickly"""
    session = SessionLocal()
    
    try:
        # Create demo buildings
        demo_buildings = [
            {"name": "Engineering Building", "type": "academic", "area": 85000},
            {"name": "Student Center", "type": "entertainment", "area": 65000},
            {"name": "Library", "type": "academic", "area": 45000},
            {"name": "Dormitory A", "type": "residential", "area": 120000},
            {"name": "Admin Building", "type": "office", "area": 35000}
        ]
        
        building_ids = []
        for i, bldg in enumerate(demo_buildings, 1):
            building = Building(
                id=i,
                name=bldg["name"],
                building_type=bldg["type"],
                area_sqft=bldg["area"],
                year_built=random.randint(1980, 2020),
                campus_id=1
            )
            session.merge(building)
            building_ids.append(i)
        
        # Generate energy readings (last 7 days)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for building_id in building_ids:
            current_time = start_time
            base_usage = random.uniform(80, 200)
            
            while current_time <= end_time:
                # Create realistic daily pattern
                hour = current_time.hour
                if 6 <= hour <= 18:  # Daytime
                    usage_multiplier = 1.2 + random.uniform(-0.2, 0.3)
                else:  # Nighttime
                    usage_multiplier = 0.6 + random.uniform(-0.1, 0.2)
                
                # Weekend reduction
                if current_time.weekday() >= 5:
                    usage_multiplier *= 0.7
                
                meter_reading = base_usage * usage_multiplier
                
                # Add some anomalies (5% chance)
                if random.random() < 0.05:
                    meter_reading *= random.uniform(2, 3)
                
                reading = EnergyReading(
                    building_id=building_id,
                    timestamp=current_time,
                    meter_reading=meter_reading,
                    meter_type=0,
                    air_temperature=70 + random.uniform(-10, 15),
                    cost_usd=meter_reading * 0.12,
                    carbon_emissions_lbs=meter_reading * 0.92
                )
                session.add(reading)
                
                current_time += timedelta(hours=1)
        
        session.commit()
        print("✅ Demo data generated successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_demo_data()