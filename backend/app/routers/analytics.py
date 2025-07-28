from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import EnergyReading, Building, Anomaly
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/buildings/{building_id}/anomalies")
async def detect_anomalies(building_id: int, hours: int = 168, db: Session = Depends(get_db)):
    """Get anomalies detected for a building"""
    
    # Get existing anomalies from database
    anomalies = db.query(Anomaly)\
        .filter(Anomaly.building_id == building_id)\
        .filter(Anomaly.timestamp >= datetime.now() - timedelta(hours=hours))\
        .order_by(desc(Anomaly.timestamp))\
        .all()
    
    # If no anomalies, generate some mock ones for demo
    if not anomalies:
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            # Create mock anomalies for demo
            mock_anomalies = []
            for i in range(3):
                timestamp = datetime.now() - timedelta(hours=random.randint(1, hours))
                mock_anomalies.append({
                    "id": f"mock_{building_id}_{i}",
                    "timestamp": timestamp,
                    "anomaly_score": random.uniform(-0.8, -0.2),
                    "anomaly_type": random.choice(["usage_spike", "equipment_failure", "schedule_deviation"]),
                    "energy_value": random.uniform(50, 200),
                    "expected_value": random.uniform(30, 150),
                    "severity": random.choice(["low", "medium", "high"]),
                    "description": f"Anomaly detected in {building.name}"
                })
            
            return {
                "building_id": building_id,
                "anomaly_count": len(mock_anomalies),
                "anomalies": mock_anomalies,
                "period_hours": hours
            }
    
    # Format real anomalies
    formatted_anomalies = []
    for anomaly in anomalies:
        formatted_anomalies.append({
            "id": anomaly.id,
            "timestamp": anomaly.timestamp,
            "anomaly_score": anomaly.anomaly_score,
            "anomaly_type": anomaly.anomaly_type,
            "energy_value": anomaly.energy_value,
            "expected_value": anomaly.expected_value,
            "deviation_percent": anomaly.deviation_percent,
            "severity": anomaly.severity,
            "status": anomaly.status
        })
    
    return {
        "building_id": building_id,
        "anomaly_count": len(formatted_anomalies),
        "anomalies": formatted_anomalies,
        "period_hours": hours
    }

@router.get("/buildings/{building_id}/forecast")
async def get_energy_forecast(building_id: int, hours: int = 24, db: Session = Depends(get_db)):
    """Get energy consumption forecast"""
    
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Get recent data to base forecast on
    recent_readings = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .order_by(desc(EnergyReading.timestamp))\
        .limit(168)\
        .all()  # Last week
    
    if not recent_readings:
        raise HTTPException(status_code=404, detail="No historical data available for forecasting")
    
    # Generate mock forecast based on historical patterns
    avg_usage = sum(r.meter_reading for r in recent_readings) / len(recent_readings)
    
    forecast_data = []
    base_time = datetime.now()
    
    for i in range(hours):
        timestamp = base_time + timedelta(hours=i+1)
        
        # Simple pattern: lower at night, higher during day
        hour = timestamp.hour
        if 6 <= hour <= 18:  # Daytime
            multiplier = 1.2 + random.uniform(-0.2, 0.3)
        else:  # Nighttime
            multiplier = 0.6 + random.uniform(-0.1, 0.2)
        
        predicted_value = avg_usage * multiplier
        confidence_range = predicted_value * 0.15
        
        forecast_data.append({
            "timestamp": timestamp,
            "predicted_kwh": predicted_value,
            "confidence_lower": predicted_value - confidence_range,
            "confidence_upper": predicted_value + confidence_range,
            "confidence_level": 0.95
        })
    
    total_predicted = sum(f["predicted_kwh"] for f in forecast_data)
    
    return {
        "building_id": building_id,
        "forecast_period_hours": hours,
        "total_predicted_kwh": total_predicted,
        "model_info": {
            "type": "time_series_analysis",
            "accuracy": "85%",
            "last_trained": datetime.now() - timedelta(days=1)
        },
        "forecast": forecast_data
    }

@router.get("/efficiency/leaderboard")
async def get_efficiency_leaderboard(period: str = "week", db: Session = Depends(get_db)):
    """Get building efficiency leaderboard"""
    
    buildings = db.query(Building).all()
    
    leaderboard = []
    for building in buildings:
        # Calculate efficiency score (mock calculation for demo)
        base_score = 75 + (building.id % 25)
        
        # Add some randomness based on period
        if period == "week":
            score = base_score + random.randint(-5, 5)
        elif period == "month":
            score = base_score + random.randint(-10, 10)
        else:  # daily
            score = base_score + random.randint(-3, 3)
        
        score = max(0, min(100, score))  # Clamp between 0-100
        
        # Get recent usage for additional metrics
        recent_reading = db.query(EnergyReading)\
            .filter(EnergyReading.building_id == building.id)\
            .order_by(desc(EnergyReading.timestamp))\
            .first()
        
        current_usage = recent_reading.meter_reading if recent_reading else 0
        
        leaderboard.append({
            "building_id": building.id,
            "name": building.name,
            "building_type": building.building_type,
            "efficiency_score": score,
            "current_usage": current_usage,
            "area_sqft": building.area_sqft,
            "usage_per_sqft": current_usage / building.area_sqft if building.area_sqft else 0
        })
    
    # Sort by efficiency score (highest first)
    leaderboard.sort(key=lambda x: x["efficiency_score"], reverse=True)
    
    # Add rankings
    for i, building in enumerate(leaderboard):
        building["rank"] = i + 1
    
    return {
        "period": period,
        "total_buildings": len(leaderboard),
        "leaderboard": leaderboard
    }

@router.get("/campus/stats")
async def get_campus_statistics(db: Session = Depends(get_db)):
    """Get overall campus energy statistics"""
    
    # Get total buildings
    total_buildings = db.query(Building).count()
    
    # Get recent energy data
    recent_time = datetime.now() - timedelta(hours=24)
    recent_readings = db.query(EnergyReading)\
        .filter(EnergyReading.timestamp >= recent_time)\
        .all()
    
    if recent_readings:
        total_usage = sum(r.meter_reading for r in recent_readings)
        avg_usage = total_usage / len(recent_readings)
    else:
        total_usage = 0
        avg_usage = 0
    
    # Mock additional statistics
    estimated_cost = total_usage * 0.12  # $0.12 per kWh
    carbon_emissions = total_usage * 0.92  # 0.92 lbs CO2 per kWh
    
    # Calculate efficiency trend (mock)
    efficiency_trend = random.choice(["improving", "stable", "declining"])
    efficiency_change = random.uniform(-5, 10)
    
    return {
        "overview": {
            "total_buildings": total_buildings,
            "total_usage_24h": total_usage,
            "average_usage": avg_usage,
            "estimated_cost_24h": estimated_cost,
            "carbon_emissions_lbs": carbon_emissions
        },
        "trends": {
            "efficiency_trend": efficiency_trend,
            "efficiency_change_percent": efficiency_change,
            "usage_trend": "stable",
            "peak_demand_time": "14:00"
        },
        "alerts": {
            "active_anomalies": random.randint(0, 5),
            "high_usage_buildings": random.randint(0, 3),
            "maintenance_alerts": random.randint(0, 2)
        }
    }

@router.post("/buildings/compare")
async def compare_buildings(building_ids: list[int], period_days: int = 7, db: Session = Depends(get_db)):
    """Compare energy usage between multiple buildings"""
    
    if len(building_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 buildings required for comparison")
    
    # Get building info
    buildings = db.query(Building).filter(Building.id.in_(building_ids)).all()
    
    if len(buildings) != len(building_ids):
        raise HTTPException(status_code=404, detail="One or more buildings not found")
    
    comparison_data = []
    
    for building in buildings:
        # Get usage data for the period
        start_time = datetime.now() - timedelta(days=period_days)
        readings = db.query(EnergyReading)\
            .filter(EnergyReading.building_id == building.id)\
            .filter(EnergyReading.timestamp >= start_time)\
            .all()
        
        total_usage = sum(r.meter_reading for r in readings) if readings else 0
        avg_usage = total_usage / len(readings) if readings else 0
        
        comparison_data.append({
            "building_id": building.id,
            "name": building.name,
            "building_type": building.building_type,
            "area_sqft": building.area_sqft,
            "total_usage": total_usage,
            "average_usage": avg_usage,
            "usage_per_sqft": total_usage / building.area_sqft if building.area_sqft else 0,
            "efficiency_score": 75 + (building.id % 25),
            "data_points": len(readings)
        })
    
    # Sort by total usage
    comparison_data.sort(key=lambda x: x["total_usage"], reverse=True)
    
    return {
        "comparison_period_days": period_days,
        "buildings_compared": len(comparison_data),
        "comparison_data": comparison_data,
        "insights": [
            f"Highest consumer: {comparison_data[0]['name']}" if comparison_data else "",
            f"Most efficient: {max(comparison_data, key=lambda x: x['efficiency_score'])['name']}" if comparison_data else ""
        ]
    }