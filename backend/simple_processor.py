#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleASHRAEProcessor:
    def __init__(self):
        # Database connection
        self.database_url = "postgresql://postgres:password@greenpulse-db:5432/greenpulse"
        self.engine = create_engine(self.database_url)
        
        # Data file paths
        self.data_dir = "/app/ashrae-energy-data"
        
    def process_sample_data(self):
        """Process a sample of ASHRAE data for demo"""
        logger.info("🚀 Starting sample ASHRAE data processing...")
        
        try:
            # Process building metadata
            self.process_buildings()
            
            # Process energy readings
            self.process_energy_data()
            
            logger.info("✅ Sample data processing completed!")
            
        except Exception as e:
            logger.error(f"❌ Error processing data: {e}")
            raise
    
    def process_buildings(self):
        """Process building metadata"""
        logger.info("📋 Processing building metadata...")
        
        metadata_file = os.path.join(self.data_dir, "building_metadata.csv")
        
        if not os.path.exists(metadata_file):
            logger.error(f"❌ Building metadata file not found: {metadata_file}")
            return
        
        # Read metadata
        df = pd.read_csv(metadata_file)
        logger.info(f"📊 Loaded {len(df)} buildings from metadata")
        
        # Clean data
        df = df.fillna({
            'year_built': 2000,
            'floor_count': 1,
            'square_feet': 10000
        })
        
        # Take first 50 buildings for demo
        df = df.head(50)
        
        with self.engine.connect() as conn:
            # Clear existing data
            conn.execute(text("DELETE FROM energy_readings"))
            conn.execute(text("DELETE FROM buildings"))
            conn.commit()
            
            # Insert buildings
            for _, row in df.iterrows():
                building_type = self.map_building_type(row['primary_use'])
                
                query = text("""
                    INSERT INTO buildings (
                        id, campus_id, name, building_type, primary_use, 
                        area_sqft, floors, year_built, site_id
                    ) VALUES (
                        :id, :campus_id, :name, :building_type, :primary_use,
                        :area_sqft, :floors, :year_built, :site_id
                    ) ON CONFLICT (id) DO NOTHING
                """)
                
                conn.execute(query, {
                    'id': int(row['building_id']),
                    'campus_id': 0,
                    'name': f"{row['primary_use']} Building {row['building_id']}",
                    'building_type': building_type,
                    'primary_use': row['primary_use'],
                    'area_sqft': int(row['square_feet']),
                    'floors': int(row['floor_count']) if pd.notna(row['floor_count']) else 1,
                    'year_built': int(row['year_built']) if pd.notna(row['year_built']) else 2000,
                    'site_id': int(row['site_id'])
                })
            
            conn.commit()
            logger.info(f"✅ Successfully processed {len(df)} buildings")
    
    def process_energy_data(self):
        """Process energy readings"""
        logger.info("⚡ Processing energy readings...")
        
        train_file = os.path.join(self.data_dir, "train.csv")
        
        if not os.path.exists(train_file):
            logger.error(f"❌ Training data file not found: {train_file}")
            return
        
        # Process in small chunks for demo
        chunk_size = 10000
        total_processed = 0
        max_records = 100000  # Limit for demo
        
        with self.engine.connect() as conn:
            for chunk_num, chunk in enumerate(pd.read_csv(train_file, chunksize=chunk_size)):
                
                if total_processed >= max_records:
                    break
                
                # Filter to our demo buildings (first 50)
                chunk = chunk[chunk['building_id'] <= 50]
                
                if len(chunk) == 0:
                    continue
                
                # Take only what we need
                remaining = max_records - total_processed
                if len(chunk) > remaining:
                    chunk = chunk.head(remaining)
                
                logger.info(f"🔄 Processing chunk {chunk_num + 1}: {len(chunk)} records")
                
                # Clean data
                chunk['timestamp'] = pd.to_datetime(chunk['timestamp'])
                chunk['meter_reading'] = chunk['meter_reading'].fillna(0)
                chunk = chunk[chunk['meter_reading'] >= 0]
                
                # Insert in batches
                batch_size = 1000
                for i in range(0, len(chunk), batch_size):
                    batch = chunk.iloc[i:i + batch_size]
                    self.insert_energy_batch(conn, batch)
                
                total_processed += len(chunk)
                logger.info(f"📈 Processed {total_processed} total records")
                
                if total_processed >= max_records:
                    break
            
            conn.commit()
            logger.info(f"✅ Successfully processed {total_processed} energy readings")
    
    def insert_energy_batch(self, conn, batch_df):
        """Insert a batch of energy readings"""
        
        query = text("""
            INSERT INTO energy_readings (
                building_id, timestamp, meter_type, meter_reading,
                cost_usd, carbon_emissions_lbs, efficiency_score
            ) VALUES (
                :building_id, :timestamp, :meter_type, :meter_reading,
                :cost_usd, :carbon_emissions_lbs, :efficiency_score
            )
        """)
        
        records = []
        for _, row in batch_df.iterrows():
            records.append({
                'building_id': int(row['building_id']),
                'timestamp': row['timestamp'],
                'meter_type': int(row['meter']),
                'meter_reading': float(row['meter_reading']),
                'cost_usd': float(row['meter_reading']) * 0.12,  # $0.12 per kWh
                'carbon_emissions_lbs': float(row['meter_reading']) * 0.92,  # 0.92 lbs CO2 per kWh
                'efficiency_score': 75 + (int(row['building_id']) % 25)  # Mock efficiency
            })
        
        conn.execute(query, records)
    
    def map_building_type(self, primary_use):
        """Map ASHRAE primary use to our building types"""
        mapping = {
            'Education': 'academic',
            'Office': 'office',
            'Lodging/residential': 'residential',
            'Entertainment/public assembly': 'entertainment',
            'Public services': 'public',
            'Healthcare': 'healthcare',
            'Retail': 'retail',
            'Warehouse/storage': 'warehouse',
            'Food sales and service': 'food_service',
            'Religious worship': 'religious',
            'Manufacturing/industrial': 'industrial',
            'Parking': 'parking',
            'Other': 'other'
        }
        return mapping.get(primary_use, 'other')
    
    def get_summary(self):
        """Get data summary"""
        with self.engine.connect() as conn:
            buildings = conn.execute(text("SELECT COUNT(*) FROM buildings")).scalar()
            readings = conn.execute(text("SELECT COUNT(*) FROM energy_readings")).scalar()
            
            return {
                'buildings': buildings,
                'energy_readings': readings
            }

def main():
    processor = SimpleASHRAEProcessor()
    
    logger.info("🌱 GreenPulse Sample Data Pipeline Starting...")
    
    try:
        processor.process_sample_data()
        
        # Print summary
        summary = processor.get_summary()
        logger.info("📈 Data Processing Summary:")
        logger.info(f"   Buildings: {summary['buildings']:,}")
        logger.info(f"   Energy Readings: {summary['energy_readings']:,}")
        
        logger.info("🎉 Sample data pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()