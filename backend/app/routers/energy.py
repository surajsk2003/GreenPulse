from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.database import EnergyReading, Building
from sqlalchemy import func, desc, and_

router = APIRouter()

@router.get("/buildings/{building_id}/current")
async def get_current_energy(building_id: int, db: Session = Depends(get_db)):
    """Get current energy consumption for a building"""
    # Get latest reading
    latest_reading = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .order_by(desc(EnergyReading.timestamp))\
        .first()
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No energy data found for this building")
    
    # Calculate efficiency score (mock calculation)
    building = db.query(Building).filter(Building.id == building_id).first()
    efficiency_score = 75 + (building_id % 25) if building else 50
    
    return {
        "building_id": building_id,
        "timestamp": latest_reading.timestamp,
        "meter_reading": latest_reading.meter_reading,
        "meter_type": latest_reading.meter_type,
        "air_temperature": latest_reading.air_temperature,
        "efficiency_score": efficiency_score,
        "status": "normal" if efficiency_score > 70 else "attention_needed"
    }

@router.get("/buildings/{building_id}/historical")
async def get_historical_energy(
    building_id: int,
    hours: int = Query(24, ge=1, le=8760),  # Max 1 year
    meter_type: Optional[int] = Query(None, ge=0, le=3),
    db: Session = Depends(get_db)
):
    """Get historical energy data"""
    
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Build query
    query = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .filter(EnergyReading.timestamp >= start_time)\
        .filter(EnergyReading.timestamp <= end_time)
    
    if meter_type is not None:
        query = query.filter(EnergyReading.meter_type == meter_type)
    
    readings = query.order_by(EnergyReading.timestamp).all()
    
    if not readings:
        return {
            "building_id": building_id,
            "period": {"start": start_time, "end": end_time},
            "readings": [],
            "summary": {"total_readings": 0, "avg_usage": 0, "max_usage": 0}
        }
    
    # Calculate summary statistics
    meter_readings = [r.meter_reading for r in readings]
    summary = {
        "total_readings": len(readings),
        "avg_usage": sum(meter_readings) / len(meter_readings),
        "max_usage": max(meter_readings),
        "min_usage": min(meter_readings)
    }
    
    return {
        "building_id": building_id,
        "period": {"start": start_time, "end": end_time},
        "readings": [
            {
                "timestamp": r.timestamp,
                "meter_reading": r.meter_reading,
                "meter_type": r.meter_type,
                "air_temperature": r.air_temperature
            }
            for r in readings
        ],
        "summary": summary
    }

@router.get("/buildings/{building_id}/daily-pattern")
async def get_daily_energy_pattern(building_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get daily energy usage patterns"""
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    readings = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .filter(EnergyReading.timestamp >= start_time)\
        .order_by(EnergyReading.timestamp)\
        .all()
    
    if not readings:
        return {"building_id": building_id, "pattern": []}
    
    # Group by hour of day
    hourly_usage = {}
    for reading in readings:
        hour = reading.timestamp.hour
        if hour not in hourly_usage:
            hourly_usage[hour] = []
        hourly_usage[hour].append(reading.meter_reading)
    
    # Calculate average for each hour
    pattern = []
    for hour in range(24):
        if hour in hourly_usage:
            avg_usage = sum(hourly_usage[hour]) / len(hourly_usage[hour])
        else:
            avg_usage = 0
        pattern.append({
            "hour": hour,
            "average_usage": avg_usage,
            "data_points": len(hourly_usage.get(hour, []))
        })
    
    return {
        "building_id": building_id,
        "period_days": days,
        "pattern": pattern
    }

@router.get("/buildings/{building_id}/comparison")
async def compare_energy_usage(
    building_id: int,
    compare_days: int = 7,
    baseline_days: int = 7,
    db: Session = Depends(get_db)
):
    """Compare current period vs baseline period"""
    
    # Current period
    current_end = datetime.now()
    current_start = current_end - timedelta(days=compare_days)
    
    # Baseline period (previous period)
    baseline_end = current_start
    baseline_start = baseline_end - timedelta(days=baseline_days)
    
    # Get current period data
    current_readings = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .filter(and_(
            EnergyReading.timestamp >= current_start,
            EnergyReading.timestamp <= current_end
        ))\
        .all()
    
    # Get baseline period data
    baseline_readings = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .filter(and_(
            EnergyReading.timestamp >= baseline_start,
            EnergyReading.timestamp <= baseline_end
        ))\
        .all()
    
    if not current_readings or not baseline_readings:
        return {
            "building_id": building_id,
            "comparison": "insufficient_data"
        }
    
    # Calculate totals
    current_total = sum(r.meter_reading for r in current_readings)
    baseline_total = sum(r.meter_reading for r in baseline_readings)
    
    # Calculate percentage change
    change_percent = ((current_total - baseline_total) / baseline_total * 100) if baseline_total > 0 else 0
    
    return {
        "building_id": building_id,
        "current_period": {
            "start": current_start,
            "end": current_end,
            "total_usage": current_total,
            "reading_count": len(current_readings)
        },
        "baseline_period": {
            "start": baseline_start,
            "end": baseline_end,
            "total_usage": baseline_total,
            "reading_count": len(baseline_readings)
        },
        "comparison": {
            "change_percent": change_percent,
            "trend": "increasing" if change_percent > 0 else "decreasing",
            "significance": "high" if abs(change_percent) > 10 else "moderate" if abs(change_percent) > 5 else "low"
        }
    }

@router.get("/campus/overview")
async def get_campus_energy_overview(db: Session = Depends(get_db)):
    """Get overall campus energy overview"""
    
    # Get all buildings
    buildings = db.query(Building).all()
    
    # Get latest readings for each building
    campus_data = []
    total_current_usage = 0
    
    for building in buildings:
        latest_reading = db.query(EnergyReading)\
            .filter(EnergyReading.building_id == building.id)\
            .order_by(desc(EnergyReading.timestamp))\
            .first()
        
        current_usage = latest_reading.meter_reading if latest_reading else 0
        total_current_usage += current_usage
        
        campus_data.append({
            "building_id": building.id,
            "name": building.name,
            "building_type": building.building_type,
            "current_usage": current_usage,
            "efficiency_score": 75 + (building.id % 25)
        })
    
    # Sort by usage (highest first)
    campus_data.sort(key=lambda x: x["current_usage"], reverse=True)
    
    return {
        "total_buildings": len(buildings),
        "total_current_usage": total_current_usage,
        "average_efficiency": sum(b["efficiency_score"] for b in campus_data) / len(campus_data) if campus_data else 0,
        "top_consumers": campus_data[:5],
        "buildings_summary": campus_data
    }