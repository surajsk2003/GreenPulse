"""
ML Analytics endpoints for GreenPulse
Provides anomaly detection, forecasting, and insights
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add ML models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml-models'))

from app.core.database import get_db
from app.models.database import Building, EnergyReading

# Try to import ML models (they might not be available in all environments)
try:
    from anomaly_detector import EnergyAnomalyDetector
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("ML models not available - using mock implementations")

router = APIRouter(prefix="/api/ml", tags=["ml-analytics"])
logger = logging.getLogger(__name__)

# Global ML model instances (in production, these would be loaded from saved models)
_anomaly_detector = None

def get_anomaly_detector():
    """Get or create anomaly detector instance"""
    global _anomaly_detector
    if _anomaly_detector is None and ML_AVAILABLE:
        _anomaly_detector = EnergyAnomalyDetector(contamination=0.1)
    return _anomaly_detector

@router.post("/anomaly-detection/train/{building_id}")
async def train_anomaly_model(
    building_id: int,
    db: Session = Depends(get_db),
    days_back: int = Query(30, description="Days of historical data to use for training")
):
    """
    Train anomaly detection model for a specific building
    """
    try:
        # Get training data
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = text("""
            SELECT timestamp, building_id, meter_reading, 
                   air_temperature, wind_speed, cloud_coverage
            FROM energy_readings 
            WHERE building_id = :building_id 
            AND timestamp >= :cutoff_date
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"building_id": building_id, "cutoff_date": cutoff_date})
        data = result.fetchall()
        
        if len(data) < 100:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient data for training: {len(data)} records (minimum 100 required)"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'building_id', 'meter_reading', 
            'air_temperature', 'wind_speed', 'cloud_coverage'
        ])
        
        if not ML_AVAILABLE:
            # Mock response when ML models aren't available
            return {
                "status": "success",
                "message": "Mock training completed (ML models not available)",
                "building_id": building_id,
                "training_samples": len(df),
                "model_metrics": {
                    "training_samples": len(df),
                    "feature_count": 10,
                    "anomaly_rate": 0.1,
                    "contamination": 0.1
                }
            }
        
        # Train the model
        detector = get_anomaly_detector()
        metrics = detector.fit(df, building_id=building_id)
        
        return {
            "status": "success",
            "message": "Anomaly detection model trained successfully",
            "building_id": building_id,
            "training_samples": len(df),
            "model_metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error training anomaly model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomaly-detection/{building_id}")
async def detect_anomalies(
    building_id: int,
    db: Session = Depends(get_db),
    hours_back: int = Query(24, description="Hours of recent data to analyze"),
    train_if_needed: bool = Query(True, description="Train model if not already trained")
):
    """
    Detect anomalies in recent energy data for a building
    """
    try:
        # Get recent data for analysis
        cutoff_date = datetime.now() - timedelta(hours=hours_back)
        
        query = text("""
            SELECT timestamp, building_id, meter_reading, 
                   air_temperature, wind_speed, cloud_coverage
            FROM energy_readings 
            WHERE building_id = :building_id 
            AND timestamp >= :cutoff_date
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"building_id": building_id, "cutoff_date": cutoff_date})
        data = result.fetchall()
        
        if len(data) == 0:
            return {
                "building_id": building_id,
                "anomalies": [],
                "anomaly_count": 0,
                "total_points": 0,
                "anomaly_rate": 0.0,
                "message": "No recent data available"
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'building_id', 'meter_reading', 
            'air_temperature', 'wind_speed', 'cloud_coverage'
        ])
        
        if not ML_AVAILABLE:
            # Mock anomaly detection when ML models aren't available
            mock_anomalies = []
            if len(df) > 10:
                # Create a few mock anomalies
                anomaly_indices = np.random.choice(len(df), size=max(1, len(df)//20), replace=False)
                for idx in anomaly_indices:
                    row = df.iloc[idx]
                    mock_anomalies.append({
                        "timestamp": row['timestamp'],
                        "anomaly_score": float(np.random.uniform(-0.8, -0.2)),
                        "energy_value": float(row['meter_reading']),
                        "expected_value": float(row['meter_reading'] * 0.8),
                        "deviation_percent": float(np.random.uniform(50, 150)),
                        "severity": np.random.choice(['low', 'medium', 'high']),
                        "anomaly_type": np.random.choice(['usage_spike', 'off_hours_spike', 'weekend_anomaly']),
                        "building_id": building_id
                    })
            
            return {
                "building_id": building_id,
                "anomalies": mock_anomalies,
                "anomaly_count": len(mock_anomalies),
                "total_points": len(df),
                "anomaly_rate": len(mock_anomalies) / len(df) if len(df) > 0 else 0.0,
                "message": "Mock anomaly detection (ML models not available)"
            }
        
        # Check if model is trained
        detector = get_anomaly_detector()
        if not detector.is_fitted and train_if_needed:
            # Train with more historical data
            training_cutoff = datetime.now() - timedelta(days=30)
            training_query = text("""
                SELECT timestamp, building_id, meter_reading, 
                       air_temperature, wind_speed, cloud_coverage
                FROM energy_readings 
                WHERE building_id = :building_id 
                AND timestamp >= :cutoff_date
                ORDER BY timestamp
            """)
            
            training_result = db.execute(training_query, {
                "building_id": building_id, 
                "cutoff_date": training_cutoff
            })
            training_data = training_result.fetchall()
            
            if len(training_data) >= 100:
                training_df = pd.DataFrame(training_data, columns=[
                    'timestamp', 'building_id', 'meter_reading', 
                    'air_temperature', 'wind_speed', 'cloud_coverage'
                ])
                detector.fit(training_df, building_id=building_id)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient historical data for model training"
                )
        
        if not detector.is_fitted:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Set train_if_needed=true or train manually first."
            )
        
        # Detect anomalies
        results = detector.predict(df, building_id=building_id)
        results["building_id"] = building_id
        
        return results
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{building_id}")
async def generate_ai_insights(
    building_id: int,
    db: Session = Depends(get_db),
    days_back: int = Query(7, description="Days of data to analyze for insights")
):
    """
    Generate AI-powered insights for a building's energy usage
    """
    try:
        # Get building info
        building = db.query(Building).filter(Building.id == building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        
        # Get recent energy data
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        query = text("""
            SELECT 
                timestamp,
                meter_reading,
                EXTRACT(hour FROM timestamp) as hour,
                EXTRACT(dow FROM timestamp) as day_of_week,
                cost_usd,
                carbon_emissions_lbs
            FROM energy_readings 
            WHERE building_id = :building_id 
            AND timestamp >= :cutoff_date
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"building_id": building_id, "cutoff_date": cutoff_date})
        data = result.fetchall()
        
        if len(data) == 0:
            return {
                "building_id": building_id,
                "building_name": building.name,
                "insights": ["No recent data available for analysis"],
                "recommendations": [],
                "metrics": {}
            }
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data, columns=[
            'timestamp', 'meter_reading', 'hour', 'day_of_week', 'cost_usd', 'carbon_emissions_lbs'
        ])
        
        # Generate insights
        insights = []
        recommendations = []
        
        # Usage pattern analysis
        avg_usage = df['meter_reading'].mean()
        peak_hour = df.groupby('hour')['meter_reading'].mean().idxmax()
        low_hour = df.groupby('hour')['meter_reading'].mean().idxmin()
        
        insights.append(f"Average energy usage: {avg_usage:.1f} kWh")
        insights.append(f"Peak usage occurs at {peak_hour}:00")
        insights.append(f"Lowest usage at {low_hour}:00")
        
        # Weekend vs weekday analysis
        weekday_avg = df[df['day_of_week'].isin([1,2,3,4,5])]['meter_reading'].mean()
        weekend_avg = df[df['day_of_week'].isin([0,6])]['meter_reading'].mean()
        
        if weekend_avg > weekday_avg * 0.7:
            insights.append(f"High weekend usage detected: {weekend_avg:.1f} kWh vs {weekday_avg:.1f} kWh weekdays")
            recommendations.append("Review weekend equipment schedules - consider shutting down non-essential systems")
        
        # Off-hours analysis
        business_hours = df[df['hour'].between(8, 18)]
        off_hours = df[~df['hour'].between(8, 18)]
        
        if len(off_hours) > 0 and len(business_hours) > 0:
            off_hours_ratio = off_hours['meter_reading'].mean() / business_hours['meter_reading'].mean()
            if off_hours_ratio > 0.5:
                insights.append(f"Off-hours usage is {off_hours_ratio:.1%} of business hours usage")
                recommendations.append("High off-hours energy consumption detected - check for equipment left running")
        
        # Cost and environmental impact
        total_cost = df['cost_usd'].sum()
        total_emissions = df['carbon_emissions_lbs'].sum()
        
        insights.append(f"Energy cost over {days_back} days: ${total_cost:.2f}")
        insights.append(f"Carbon emissions: {total_emissions:.1f} lbs CO2")
        
        # Efficiency recommendations based on building type
        if building.building_type == 'academic':
            recommendations.append("Consider implementing smart classroom scheduling to reduce unused space heating/cooling")
        elif building.building_type == 'office':
            recommendations.append("Implement automatic equipment shutdown policies for workstations and monitors")
        elif building.building_type == 'residential':
            recommendations.append("Install smart thermostats and educate residents on energy-efficient practices")
        
        # Usage trend analysis
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_usage = df.groupby('date')['meter_reading'].sum()
        
        if len(daily_usage) > 3:
            recent_avg = daily_usage.tail(3).mean()
            earlier_avg = daily_usage.head(len(daily_usage)-3).mean()
            
            if recent_avg > earlier_avg * 1.1:
                insights.append("Energy usage trending upward in recent days")
                recommendations.append("Investigate recent changes in building operations or occupancy")
            elif recent_avg < earlier_avg * 0.9:
                insights.append("Energy usage trending downward - good progress!")
        
        # Calculate efficiency score relative to building size
        usage_per_sqft = avg_usage / building.area_sqft if building.area_sqft > 0 else 0
        
        metrics = {
            "average_usage_kwh": float(avg_usage),
            "peak_hour": int(peak_hour),
            "usage_per_sqft": float(usage_per_sqft),
            "weekend_weekday_ratio": float(weekend_avg / weekday_avg) if weekday_avg > 0 else 0,
            "total_cost": float(total_cost),
            "total_emissions_lbs": float(total_emissions),
            "efficiency_score": building.efficiency_score if hasattr(building, 'efficiency_score') else 75
        }
        
        return {
            "building_id": building_id,
            "building_name": building.name,
            "building_type": building.building_type,
            "analysis_period_days": days_back,
            "insights": insights,
            "recommendations": recommendations,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
async def get_efficiency_leaderboard(
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of buildings to return")
):
    """
    Get building efficiency leaderboard
    """
    try:
        query = text("""
            SELECT 
                b.id,
                b.name,
                b.building_type,
                b.area_sqft,
                AVG(er.meter_reading) as avg_usage,
                AVG(er.efficiency_score) as avg_efficiency_score,
                SUM(er.cost_usd) as total_cost,
                SUM(er.carbon_emissions_lbs) as total_emissions,
                COUNT(er.id) as reading_count
            FROM buildings b
            LEFT JOIN energy_readings er ON b.id = er.building_id
            WHERE er.timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY b.id, b.name, b.building_type, b.area_sqft
            HAVING COUNT(er.id) > 0
            ORDER BY avg_efficiency_score DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {"limit": limit})
        data = result.fetchall()
        
        leaderboard = []
        for i, row in enumerate(data, 1):
            usage_per_sqft = row.avg_usage / row.area_sqft if row.area_sqft > 0 else 0
            
            leaderboard.append({
                "rank": i,
                "building_id": row.id,
                "building_name": row.name,
                "building_type": row.building_type,
                "efficiency_score": float(row.avg_efficiency_score),
                "avg_usage_kwh": float(row.avg_usage),
                "usage_per_sqft": float(usage_per_sqft),
                "total_cost_7d": float(row.total_cost),
                "total_emissions_7d": float(row.total_emissions),
                "area_sqft": int(row.area_sqft)
            })
        
        return {
            "leaderboard": leaderboard,
            "total_buildings": len(leaderboard),
            "period": "Last 7 days"
        }
        
    except Exception as e:
        logger.error(f"Error generating leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast/{building_id}")
async def forecast_energy_usage(
    building_id: int,
    db: Session = Depends(get_db),
    hours_ahead: int = Query(24, description="Hours to forecast ahead")
):
    """
    Forecast future energy usage for a building
    """
    try:
        # Get historical data for forecasting
        query = text("""
            SELECT timestamp, meter_reading
            FROM energy_readings 
            WHERE building_id = :building_id 
            AND timestamp >= NOW() - INTERVAL '30 days'
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"building_id": building_id})
        data = result.fetchall()
        
        if len(data) < 24:
            raise HTTPException(
                status_code=400,
                detail="Insufficient historical data for forecasting (minimum 24 hours required)"
            )
        
        df = pd.DataFrame(data, columns=['timestamp', 'meter_reading'])
        
        # Simple moving average forecast (in production, use Prophet or ARIMA)
        recent_avg = df.tail(24)['meter_reading'].mean()
        recent_trend = (df.tail(12)['meter_reading'].mean() - df.head(12)['meter_reading'].mean()) / 12
        
        # Generate forecast timestamps
        last_timestamp = df['timestamp'].max()
        forecast_timestamps = [
            last_timestamp + timedelta(hours=i) for i in range(1, hours_ahead + 1)
        ]
        
        # Simple forecast with hourly patterns
        forecast_values = []
        for i, ts in enumerate(forecast_timestamps):
            hour = ts.hour
            
            # Basic hourly pattern (higher during business hours)
            hour_factor = 1.0
            if 8 <= hour <= 18:
                hour_factor = 1.2
            elif 22 <= hour <= 6:
                hour_factor = 0.7
            
            # Day of week factor
            dow_factor = 1.0
            if ts.weekday() >= 5:  # Weekend
                dow_factor = 0.8
            
            base_value = recent_avg + (recent_trend * i)
            forecast_value = base_value * hour_factor * dow_factor
            
            # Add some uncertainty bounds
            uncertainty = base_value * 0.1
            
            forecast_values.append({
                "timestamp": ts,
                "predicted_usage": float(max(0, forecast_value)),
                "lower_bound": float(max(0, forecast_value - uncertainty)),
                "upper_bound": float(forecast_value + uncertainty),
                "confidence": 0.8  # Mock confidence score
            })
        
        # Calculate forecast metrics
        forecast_total = sum(f["predicted_usage"] for f in forecast_values)
        forecast_avg = forecast_total / len(forecast_values) if forecast_values else 0
        historical_avg = df.tail(hours_ahead)['meter_reading'].mean() if len(df) >= hours_ahead else recent_avg
        
        return {
            "building_id": building_id,
            "forecast_period_hours": hours_ahead,
            "forecast": forecast_values,
            "summary": {
                "predicted_total_usage": float(forecast_total),
                "predicted_avg_usage": float(forecast_avg),
                "historical_avg_usage": float(historical_avg),
                "predicted_vs_historical_change": float((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0,
                "forecast_method": "Moving Average with Patterns"
            }
        }
        
    except Exception as e:
        logger.error(f"Error forecasting energy usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))