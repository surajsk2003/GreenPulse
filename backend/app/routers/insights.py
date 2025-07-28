from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import Insight, Building, EnergyReading
from sqlalchemy import desc
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/buildings/{building_id}")
async def get_building_insights(building_id: int, db: Session = Depends(get_db)):
    """Get AI-generated insights for a building"""
    
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Get existing insights from database
    existing_insights = db.query(Insight)\
        .filter(Insight.building_id == building_id)\
        .filter(Insight.status != 'dismissed')\
        .order_by(desc(Insight.priority))\
        .limit(10)\
        .all()
    
    # If no insights exist, generate mock ones for demo
    if not existing_insights:
        mock_insights = generate_mock_insights(building)
        return {
            "building_id": building_id,
            "building_name": building.name,
            "insights_count": len(mock_insights),
            "insights": mock_insights,
            "generated_at": datetime.now()
        }
    
    # Format existing insights
    formatted_insights = []
    for insight in existing_insights:
        formatted_insights.append({
            "id": insight.id,
            "type": insight.insight_type,
            "priority": insight.priority,
            "title": insight.title,
            "description": insight.description,
            "recommendation": insight.recommendation,
            "potential_savings_usd": insight.potential_savings_usd,
            "potential_savings_kwh": insight.potential_savings_kwh,
            "confidence_score": insight.confidence_score,
            "actionable_steps": insight.actionable_steps,
            "category": insight.category,
            "status": insight.status,
            "created_at": insight.created_at
        })
    
    return {
        "building_id": building_id,
        "building_name": building.name,
        "insights_count": len(formatted_insights),
        "insights": formatted_insights,
        "generated_at": datetime.now()
    }

def generate_mock_insights(building: Building):
    """Generate mock insights for demo purposes"""
    
    insights = []
    
    # Peak usage insight
    peak_savings = random.randint(800, 1500)
    insights.append({
        "id": f"peak_{building.id}",
        "type": "peak_usage",
        "priority": 0.9,
        "title": f"High Peak Usage Detected - {building.name}",
        "description": f"Energy usage peaks at 2 PM daily in {building.name}, consuming 40% more than average during this period.",
        "recommendation": "Implement load shifting strategies and optimize HVAC scheduling during peak hours.",
        "potential_savings_usd": peak_savings,
        "potential_savings_kwh": peak_savings * 8,
        "confidence_score": 0.85,
        "actionable_steps": [
            "Schedule non-critical equipment to run during off-peak hours",
            "Adjust HVAC setpoints during peak demand periods",
            "Consider battery storage for peak shaving",
            "Implement demand response programs"
        ],
        "category": "immediate",
        "status": "new",
        "impact": "high"
    })
    
    # Weekend waste insight
    if building.building_type in ["Education", "Office"]:
        weekend_savings = random.randint(400, 800)
        insights.append({
            "id": f"weekend_{building.id}",
            "type": "weekend_waste",
            "priority": 0.75,
            "title": "Excessive Weekend Energy Usage",
            "description": f"Weekend energy usage in {building.name} is 65% of weekday usage, indicating potential equipment left running unnecessarily.",
            "recommendation": "Install automated controls and implement weekend shutdown procedures for non-essential systems.",
            "potential_savings_usd": weekend_savings,
            "potential_savings_kwh": weekend_savings * 8,
            "confidence_score": 0.78,
            "actionable_steps": [
                "Install smart switches for non-essential equipment",
                "Program HVAC systems for weekend setbacks",
                "Implement occupancy-based lighting controls",
                "Review and update equipment schedules"
            ],
            "category": "short_term",
            "status": "new",
            "impact": "medium"
        })
    
    # HVAC efficiency insight
    hvac_savings = random.randint(600, 1200)
    insights.append({
        "id": f"hvac_{building.id}",
        "type": "hvac_efficiency",
        "priority": 0.82,
        "title": "HVAC System Optimization Opportunity",
        "description": f"HVAC system in {building.name} is operating at 78% efficiency. Temperature control patterns suggest optimization potential.",
        "recommendation": "Schedule HVAC maintenance and consider smart thermostat upgrades for optimal performance.",
        "potential_savings_usd": hvac_savings,
        "potential_savings_kwh": hvac_savings * 8,
        "confidence_score": 0.72,
        "actionable_steps": [
            "Schedule comprehensive HVAC system inspection",
            "Clean and replace air filters",
            "Calibrate thermostats and sensors",
            "Consider upgrading to smart HVAC controls"
        ],
        "category": "short_term",
        "status": "new",
        "impact": "high"
    })
    
    # Equipment scheduling insight
    equipment_savings = random.randint(300, 600)
    insights.append({
        "id": f"equipment_{building.id}",
        "type": "equipment_schedule",
        "priority": 0.65,
        "title": "Equipment Scheduling Inefficiency",
        "description": f"Analysis shows equipment in {building.name} running during low-occupancy periods, leading to energy waste.",
        "recommendation": "Implement smart scheduling systems to align equipment operation with actual building occupancy.",
        "potential_savings_usd": equipment_savings,
        "potential_savings_kwh": equipment_savings * 8,
        "confidence_score": 0.68,
        "actionable_steps": [
            "Install occupancy sensors in key areas",
            "Program equipment schedules based on usage patterns",
            "Implement automatic shutdown for idle equipment",
            "Train staff on energy-efficient practices"
        ],
        "category": "long_term",
        "status": "new",
        "impact": "medium"
    })
    
    # Lighting optimization
    if building.area_sqft and building.area_sqft > 50000:  # Large buildings
        lighting_savings = random.randint(400, 700)
        insights.append({
            "id": f"lighting_{building.id}",
            "type": "lighting_optimization",
            "priority": 0.58,
            "title": "Lighting System Upgrade Opportunity",
            "description": f"Current lighting system in {building.name} could benefit from LED upgrade and smart controls.",
            "recommendation": "Upgrade to LED fixtures with daylight harvesting and occupancy controls.",
            "potential_savings_usd": lighting_savings,
            "potential_savings_kwh": lighting_savings * 8,
            "confidence_score": 0.75,
            "actionable_steps": [
                "Conduct lighting audit to identify upgrade opportunities",
                "Install LED fixtures in high-usage areas first",
                "Add daylight sensors for automatic dimming",
                "Implement occupancy-based lighting controls"
            ],
            "category": "long_term",
            "status": "new",
            "impact": "medium"
        })
    
    return insights

@router.get("/campus/summary")
async def get_campus_insights_summary(db: Session = Depends(get_db)):
    """Get summary of insights across all campus buildings"""
    
    buildings = db.query(Building).all()
    
    total_insights = 0
    total_potential_savings = 0
    insight_categories = {"immediate": 0, "short_term": 0, "long_term": 0}
    priority_distribution = {"high": 0, "medium": 0, "low": 0}
    
    campus_insights = []
    
    for building in buildings:
        # Generate insights for each building
        building_insights = generate_mock_insights(building)
        total_insights += len(building_insights)
        
        building_savings = sum(insight["potential_savings_usd"] for insight in building_insights)
        total_potential_savings += building_savings
        
        # Count categories and priorities
        for insight in building_insights:
            insight_categories[insight["category"]] += 1
            
            if insight["priority"] > 0.8:
                priority_distribution["high"] += 1
            elif insight["priority"] > 0.6:
                priority_distribution["medium"] += 1
            else:
                priority_distribution["low"] += 1
        
        campus_insights.append({
            "building_id": building.id,
            "building_name": building.name,
            "insights_count": len(building_insights),
            "potential_savings": building_savings,
            "top_insight": max(building_insights, key=lambda x: x["priority"]) if building_insights else None
        })
    
    # Sort buildings by potential savings
    campus_insights.sort(key=lambda x: x["potential_savings"], reverse=True)
    
    return {
        "campus_summary": {
            "total_buildings": len(buildings),
            "total_insights": total_insights,
            "total_potential_savings_usd": total_potential_savings,
            "avg_savings_per_building": total_potential_savings / len(buildings) if buildings else 0
        },
        "insight_breakdown": {
            "by_category": insight_categories,
            "by_priority": priority_distribution
        },
        "top_opportunities": campus_insights[:5],
        "all_buildings": campus_insights
    }

@router.post("/buildings/{building_id}/insights/{insight_id}/status")
async def update_insight_status(
    building_id: int, 
    insight_id: str, 
    status: str,
    db: Session = Depends(get_db)
):
    """Update the status of an insight (acknowledge, implement, dismiss)"""
    
    valid_statuses = ["new", "acknowledged", "implementing", "completed", "dismissed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    # For demo purposes, just return success
    # In real implementation, would update database
    
    return {
        "building_id": building_id,
        "insight_id": insight_id,
        "status": status,
        "updated_at": datetime.now(),
        "message": f"Insight status updated to '{status}'"
    }

@router.get("/insights/types")
async def get_insight_types():
    """Get available insight types and their descriptions"""
    
    return {
        "insight_types": [
            {
                "type": "peak_usage",
                "name": "Peak Usage Analysis",
                "description": "Identifies patterns of high energy consumption during peak hours",
                "potential_impact": "High",
                "typical_savings": "15-25%"
            },
            {
                "type": "weekend_waste",
                "name": "Weekend Energy Waste",
                "description": "Detects unnecessary energy consumption during low-occupancy periods",
                "potential_impact": "Medium",
                "typical_savings": "10-20%"
            },
            {
                "type": "hvac_efficiency",
                "name": "HVAC Optimization",
                "description": "Analyzes heating, ventilation, and air conditioning system performance",
                "potential_impact": "High",
                "typical_savings": "20-30%"
            },
            {
                "type": "equipment_schedule",
                "name": "Equipment Scheduling",
                "description": "Optimizes equipment operation schedules based on usage patterns",
                "potential_impact": "Medium",
                "typical_savings": "8-15%"
            },
            {
                "type": "lighting_optimization",
                "name": "Lighting System Efficiency",
                "description": "Identifies opportunities for lighting upgrades and controls",
                "potential_impact": "Medium",
                "typical_savings": "12-18%"
            }
        ]
    }