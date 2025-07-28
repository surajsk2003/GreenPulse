import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from typing import Optional
import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import settings
from backend.app.models.database import Base, Building, EnergyReading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ASHRAEProcessor:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
        # Data file paths
        self.data_dir = "ashrae-energy-data"
        
    def process_all_data(self, sample_size: Optional[int] = None):
        """Process all ASHRAE data files"""
        logger.info("🚀 Starting ASHRAE data processing...")
        
        # Step 1: Process building metadata
        self.process_building_metadata()
        
        # Step 2: Process energy readings
        self.process_energy_readings(sample_size=sample_size)
        
        logger.info("✅ ASHRAE data processing completed!")
    
    def process_building_metadata(self):
        """Process building metadata from CSV"""
        logger.info("📋 Processing building metadata...")
        
        metadata_file = os.path.join(self.data_dir, "building_metadata.csv")
        
        if not os.path.exists(metadata_file):
            logger.error(f"❌ Building metadata file not found: {metadata_file}")
            return
        
        # Read metadata
        df = pd.read_csv(metadata_file)
        logger.info(f"📊 Loaded {len(df)} buildings from metadata")
        
        # Clean and prepare data
        df = df.fillna({
            'year_built': 2000,
            'floor_count': 1,
            'square_feet': 10000
        })
        
        # Add campus_id (all buildings belong to campus 0 for now)
        df['campus_id'] = 0
        
        session = self.SessionLocal()
        try:
            # Clear existing buildings (for fresh start)
            session.query(Building).delete()
            
            # Insert buildings
            for _, row in df.iterrows():
                building = Building(
                    id=int(row['building_id']),
                    campus_id=0,
                    name=f"{row['primary_use']} Building {row['building_id']}",
                    building_type=self._map_building_type(row['primary_use']),
                    primary_use=row['primary_use'],
                    area_sqft=int(row['square_feet']),
                    floors=int(row['floor_count']) if pd.notna(row['floor_count']) else 1,
                    year_built=int(row['year_built']) if pd.notna(row['year_built']) else 2000,
                    site_id=int(row['site_id'])
                )
                session.add(building)
            
            session.commit()
            logger.info(f"✅ Successfully processed {len(df)} buildings")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error processing building metadata: {e}")
        finally:
            session.close()
    
    def process_energy_readings(self, sample_size: Optional[int] = None):
        """Process energy readings from train.csv"""
        logger.info("⚡ Processing energy readings...")
        
        train_file = os.path.join(self.data_dir, "train.csv")
        weather_file = os.path.join(self.data_dir, "weather_train.csv")
        
        if not os.path.exists(train_file):
            logger.error(f"❌ Training data file not found: {train_file}")
            return
        
        # Load weather data if available
        weather_data = None
        if os.path.exists(weather_file):
            logger.info("🌤️ Loading weather data...")
            weather_data = pd.read_csv(weather_file)
            weather_data['timestamp'] = pd.to_datetime(weather_data['timestamp'])
            logger.info(f"📊 Loaded {len(weather_data)} weather records")
        
        # Process energy data in chunks
        chunk_size = 50000
        total_processed = 0
        
        session = self.SessionLocal()
        try:
            # Clear existing readings for fresh start
            logger.info("🧹 Clearing existing energy readings...")
            session.query(EnergyReading).delete()
            session.commit()
            
            logger.info("📊 Processing energy readings in chunks...")
            
            for chunk_num, chunk in enumerate(pd.read_csv(train_file, chunksize=chunk_size)):
                
                # Apply sample size limit if specified
                if sample_size and total_processed >= sample_size:
                    logger.info(f"📋 Reached sample size limit of {sample_size} records")
                    break
                
                # If sample_size specified, limit this chunk
                if sample_size:
                    remaining = sample_size - total_processed
                    if len(chunk) > remaining:
                        chunk = chunk.head(remaining)
                
                logger.info(f"🔄 Processing chunk {chunk_num + 1}: {len(chunk)} records")
                
                # Clean and prepare chunk
                chunk = self._clean_energy_data(chunk, weather_data)
                
                # Insert records
                batch_size = 1000
                for i in range(0, len(chunk), batch_size):
                    batch = chunk.iloc[i:i + batch_size]
                    self._insert_energy_batch(session, batch)
                
                total_processed += len(chunk)
                logger.info(f"📈 Processed {total_processed} total records")
                
                # Commit every chunk
                session.commit()
            
            logger.info(f"✅ Successfully processed {total_processed} energy readings")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error processing energy readings: {e}")
            raise
        finally:
            session.close()
    
    def _clean_energy_data(self, df: pd.DataFrame, weather_data: Optional[pd.DataFrame] = None):
        """Clean and prepare energy data"""
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Handle missing values
        df['meter_reading'] = df['meter_reading'].fillna(0)
        
        # Remove negative readings (data quality issue)
        df = df[df['meter_reading'] >= 0]
        
        # Remove extreme outliers (beyond 99.9th percentile per building)
        df = df.groupby('building_id').apply(
            lambda x: x[x['meter_reading'] <= x['meter_reading'].quantile(0.999)]
        ).reset_index(drop=True)
        
        # Add weather data if available
        if weather_data is not None:
            # Merge on site_id and timestamp
            # First, get building-to-site mapping
            metadata_file = os.path.join(self.data_dir, "building_metadata.csv")
            if os.path.exists(metadata_file):
                building_meta = pd.read_csv(metadata_file)[['building_id', 'site_id']]
                df = df.merge(building_meta, on='building_id', how='left')
                
                # Merge weather data
                df = df.merge(
                    weather_data, 
                    on=['site_id', 'timestamp'], 
                    how='left'
                )
        
        return df
    
    def _insert_energy_batch(self, session, batch_df: pd.DataFrame):
        """Insert a batch of energy readings"""
        
        energy_readings = []
        
        for _, row in batch_df.iterrows():
            reading = EnergyReading(
                building_id=int(row['building_id']),
                timestamp=row['timestamp'],
                meter_type=int(row['meter']),
                meter_reading=float(row['meter_reading']),
                
                # Weather data (if available)
                air_temperature=row.get('air_temperature'),
                cloud_coverage=row.get('cloud_coverage'),
                dew_temperature=row.get('dew_temperature'),
                precip_depth_1_hr=row.get('precip_depth_1_hr'),
                sea_level_pressure=row.get('sea_level_pressure'),
                wind_direction=row.get('wind_direction'),
                wind_speed=row.get('wind_speed'),
                
                # Calculated fields (simplified for demo)
                cost_usd=float(row['meter_reading']) * 0.12,  # $0.12 per kWh
                carbon_emissions_lbs=float(row['meter_reading']) * 0.92,  # 0.92 lbs CO2 per kWh
                efficiency_score=75 + (int(row['building_id']) % 25)  # Mock efficiency
            )
            energy_readings.append(reading)
        
        session.add_all(energy_readings)
    
    def _map_building_type(self, primary_use: str) -> str:
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
    
    def get_data_summary(self):
        """Get summary of processed data"""
        session = self.SessionLocal()
        try:
            building_count = session.query(Building).count()
            reading_count = session.query(EnergyReading).count()
            
            # Get date range
            date_range = session.query(
                EnergyReading.timestamp.label('min_date'),
                EnergyReading.timestamp.label('max_date')
            ).first()
            
            return {
                'buildings': building_count,
                'energy_readings': reading_count,
                'date_range': {
                    'start': date_range.min_date if date_range else None,
                    'end': date_range.max_date if date_range else None
                }
            }
        finally:
            session.close()

def main():
    """Main function to run data processing"""
    processor = ASHRAEProcessor()
    
    # Process with sample size for demo (full dataset is huge)
    sample_size = 500000  # Process 500k records for demo
    
    logger.info("🌱 GreenPulse Data Pipeline Starting...")
    logger.info(f"📊 Sample size: {sample_size:,} records")
    
    try:
        processor.process_all_data(sample_size=sample_size)
        
        # Print summary
        summary = processor.get_data_summary()
        logger.info("📈 Data Processing Summary:")
        logger.info(f"   Buildings: {summary['buildings']:,}")
        logger.info(f"   Energy Readings: {summary['energy_readings']:,}")
        
        if summary['date_range']['start']:
            logger.info(f"   Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        
        logger.info("🎉 Data pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()