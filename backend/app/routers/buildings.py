from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.database import Building, EnergyReading
from sqlalchemy import func, desc

router = APIRouter()

@router.get("/")
async def get_buildings(db: Session = Depends(get_db)):
    """Get all buildings with basic info"""
    buildings = db.query(Building).all()
    
    result = []
    for building in buildings:
        # Get latest energy reading
        latest_reading = db.query(EnergyReading)\
            .filter(EnergyReading.building_id == building.id)\
            .order_by(desc(EnergyReading.timestamp))\
            .first()
        
        current_usage = latest_reading.meter_reading if latest_reading else 0
        
        result.append({
            "id": building.id,
            "name": building.name,
            "building_type": building.building_type,
            "primary_use": building.primary_use,
            "area_sqft": building.area_sqft,
            "year_built": building.year_built,
            "current_usage": current_usage,
            "efficiency_score": 75 + (building.id % 25)  # Mock efficiency score
        })
    
    return result

@router.get("/{building_id}")
async def get_building_details(building_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific building"""
    building = db.query(Building).filter(Building.id == building_id).first()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Get recent energy statistics
    recent_readings = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .order_by(desc(EnergyReading.timestamp))\
        .limit(168)\
        .all()  # Last week of hourly readings
    
    total_usage = sum(r.meter_reading for r in recent_readings)
    avg_usage = total_usage / len(recent_readings) if recent_readings else 0
    
    return {
        "id": building.id,
        "name": building.name,
        "building_type": building.building_type,
        "primary_use": building.primary_use,
        "area_sqft": building.area_sqft,
        "year_built": building.year_built,
        "site_id": building.site_id,
        "statistics": {
            "total_usage_week": total_usage,
            "average_hourly_usage": avg_usage,
            "readings_count": len(recent_readings),
            "efficiency_score": 75 + (building.id % 25)
        }
    }

@router.get("/{building_id}/summary")
async def get_building_summary(building_id: int, db: Session = Depends(get_db)):
    """Get building energy summary for dashboard"""
    building = db.query(Building).filter(Building.id == building_id).first()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Get latest reading
    latest_reading = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .order_by(desc(EnergyReading.timestamp))\
        .first()
    
    # Get daily average for comparison
    daily_avg = db.query(func.avg(EnergyReading.meter_reading))\
        .filter(EnergyReading.building_id == building_id)\
        .scalar() or 0
    
    current_usage = latest_reading.meter_reading if latest_reading else 0
    status = "normal"
    
    if current_usage > daily_avg * 1.3:
        status = "high"
    elif current_usage < daily_avg * 0.5:
        status = "low"
    
    return {
        "building_id": building_id,
        "name": building.name,
        "current_usage": current_usage,
        "daily_average": daily_avg,
        "status": status,
        "efficiency_score": 75 + (building.id % 25),
        "last_updated": latest_reading.timestamp if latest_reading else None
    }