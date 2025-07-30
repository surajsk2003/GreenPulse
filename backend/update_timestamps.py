#!/usr/bin/env python3
"""
Update ASHRAE data timestamps to be recent for demo purposes
"""
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_timestamps():
    """Update energy reading timestamps to be recent"""
    
    # Database connection
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/greenpulse")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Get current data timestamp range
            result = conn.execute(text("""
                SELECT 
                    MIN(timestamp) as min_ts,
                    MAX(timestamp) as max_ts,
                    COUNT(*) as count
                FROM energy_readings
            """))
            
            row = result.fetchone()
            logger.info(f"Current data: {row.count} records from {row.min_ts} to {row.max_ts}")
            
            if row.count == 0:
                logger.info("No data to update")
                return
            
            # Calculate shift needed to make max timestamp = now - 1 hour
            target_max = datetime.now() - timedelta(hours=1)
            current_max = row.max_ts
            shift_amount = target_max - current_max
            
            logger.info(f"Shifting all timestamps by {shift_amount}")
            
            # Update timestamps
            update_query = text("""
                UPDATE energy_readings 
                SET timestamp = timestamp + :shift_interval
            """)
            
            result = conn.execute(update_query, {"shift_interval": shift_amount})
            conn.commit()
            
            logger.info(f"Updated {result.rowcount} records")
            
            # Verify update
            result = conn.execute(text("""
                SELECT 
                    MIN(timestamp) as min_ts,
                    MAX(timestamp) as max_ts,
                    COUNT(*) as count
                FROM energy_readings
            """))
            
            row = result.fetchone()
            logger.info(f"Updated data: {row.count} records from {row.min_ts} to {row.max_ts}")
            
    except Exception as e:
        logger.error(f"Error updating timestamps: {e}")
        raise

if __name__ == "__main__":
    update_timestamps()