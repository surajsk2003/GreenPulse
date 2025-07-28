#!/usr/bin/env python3
"""
GreenPulse ML Models Runner
Runs anomaly detection and forecasting models for demo
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import settings
from backend.app.models.database import EnergyReading, Building, Anomaly
from backend.app.core.database import SessionLocal
from anomaly_detector import EnergyAnomalyDetector
from energy_forecaster import EnergyForecaster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_building_data(building_id: int, hours: int = 168) -> pd.DataFrame:
    """Get energy data for a building"""
    session = SessionLocal()
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        readings = session.query(EnergyReading)\
            .filter(EnergyReading.building_id == building_id)\
            .filter(EnergyReading.timestamp >= start_time)\
            .order_by(EnergyReading.timestamp)\
            .all()
        
        if not readings:
            return pd.DataFrame()
        
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.timestamp,
                'building_id': reading.building_id,
                'meter_reading': reading.meter_reading,
                'air_temperature': reading.air_temperature,
                'meter_type': reading.meter_type
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()

def run_anomaly_detection():
    """Run anomaly detection for all buildings"""
    logger.info("🔍 Running anomaly detection...")
    
    session = SessionLocal()
    try:
        buildings = session.query(Building).limit(10).all()  # Process first 10 for demo
        
        detector = EnergyAnomalyDetector(contamination=0.05)
        
        for building in buildings:
            logger.info(f"Processing building {building.id}: {building.name}")
            
            # Get data
            df = get_building_data(building.id, hours=336)  # 2 weeks
            if df.empty:
                logger.warning(f"No data for building {building.id}")
                continue
            
            # Split data for training and detection
            split_point = int(len(df) * 0.8)
            train_data = df[:split_point]
            test_data = df[split_point:]
            
            if len(train_data) < 100:
                logger.warning(f"Insufficient training data for building {building.id}")
                continue
            
            # Train model
            try:
                detector.fit(train_data, building_id=building.id)
                
                # Detect anomalies
                results = detector.predict(test_data, building_id=building.id)
                
                # Save anomalies to database
                for anomaly in results['anomalies']:
                    db_anomaly = Anomaly(
                        building_id=building.id,
                        timestamp=anomaly['timestamp'],
                        anomaly_score=anomaly['anomaly_score'],
                        anomaly_type=anomaly['anomaly_type'],
                        energy_value=anomaly['energy_value'],
                        expected_value=anomaly['expected_value'],
                        deviation_percent=anomaly['deviation_percent'],
                        severity=anomaly['severity']
                    )
                    session.add(db_anomaly)
                
                logger.info(f"✅ Found {len(results['anomalies'])} anomalies for building {building.id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing building {building.id}: {e}")
                continue
        
        session.commit()
        logger.info("🎉 Anomaly detection completed!")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Anomaly detection failed: {e}")
    finally:
        session.close()

def run_forecasting():
    """Run energy forecasting for buildings"""
    logger.info("📈 Running energy forecasting...")
    
    session = SessionLocal()
    try:
        buildings = session.query(Building).limit(5).all()  # Process first 5 for demo
        
        forecaster = EnergyForecaster()
        
        for building in buildings:
            logger.info(f"Forecasting for building {building.id}: {building.name}")
            
            # Get historical data
            df = get_building_data(building.id, hours=720)  # 30 days
            if df.empty or len(df) < 168:  # Need at least 1 week
                logger.warning(f"Insufficient data for forecasting building {building.id}")
                continue
            
            try:
                # Train and forecast
                forecast_results = forecaster.forecast(df, periods=24)  # 24 hour forecast
                
                logger.info(f"✅ Generated 24-hour forecast for building {building.id}")
                logger.info(f"   Predicted total: {forecast_results['total_predicted_kwh']:.2f} kWh")
                
            except Exception as e:
                logger.error(f"❌ Error forecasting building {building.id}: {e}")
                continue
        
        logger.info("🎉 Forecasting completed!")
        
    except Exception as e:
        logger.error(f"❌ Forecasting failed: {e}")
    finally:
        session.close()

def main():
    """Main function"""
    logger.info("🌱 GreenPulse ML Models Runner")
    logger.info("=" * 40)
    
    try:
        # Run anomaly detection
        run_anomaly_detection()
        
        # Run forecasting
        run_forecasting()
        
        logger.info("🎉 All ML models completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ ML models runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()