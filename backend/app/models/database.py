from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ARRAY, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class Campus(Base):
    __tablename__ = "campuses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    timezone = Column(String(50), default='UTC')
    total_area_sqft = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class Building(Base):
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(Integer, default=0)
    name = Column(String(255), nullable=False)
    building_type = Column(String(100))  # 'Education', 'Office', etc.
    area_sqft = Column(Integer)
    floors = Column(Integer)
    year_built = Column(Integer)
    site_id = Column(Integer)  # From ASHRAE data
    primary_use = Column(String(100))  # From ASHRAE data
    baseline_consumption_kwh = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class EnergyReading(Base):
    __tablename__ = "energy_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    meter_type = Column(Integer)  # 0=electricity, 1=chilledwater, 2=steam, 3=hotwater
    meter_reading = Column(Float, default=0)
    
    # Environmental data (from weather)
    air_temperature = Column(Float)
    cloud_coverage = Column(Float)
    dew_temperature = Column(Float)
    precip_depth_1_hr = Column(Float)
    sea_level_pressure = Column(Float)
    wind_direction = Column(Float)
    wind_speed = Column(Float)
    
    # Calculated fields  
    total_energy_btu = Column(Float)
    cost_usd = Column(Float)
    carbon_emissions_lbs = Column(Float)
    efficiency_score = Column(Float)
    
    created_at = Column(DateTime, server_default=func.now())

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(Integer, default=0)
    name = Column(String(255), nullable=False)
    building_ids = Column(ARRAY(Integer))
    energy_budget_annual = Column(Float)
    reduction_target_percent = Column(Float, default=10.0)
    current_score = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False)
    model_type = Column(String(100))  # 'anomaly_detection', 'forecasting'
    building_id = Column(Integer)
    model_version = Column(String(50))
    model_parameters = Column(JSON)
    accuracy_score = Column(Float)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, nullable=False, index=True)
    model_id = Column(Integer)
    timestamp = Column(DateTime, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    anomaly_type = Column(String(100))
    energy_value = Column(Float)
    expected_value = Column(Float)
    deviation_percent = Column(Float)
    severity = Column(String(20), default='medium')
    status = Column(String(50), default='new')
    created_at = Column(DateTime, server_default=func.now())

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, nullable=False, index=True)
    insight_type = Column(String(100))
    priority = Column(Float, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    recommendation = Column(Text)
    potential_savings_usd = Column(Float)
    potential_savings_kwh = Column(Float)
    confidence_score = Column(Float)
    actionable_steps = Column(JSON)
    category = Column(String(100))
    status = Column(String(50), default='new')
    created_at = Column(DateTime, server_default=func.now())

class Challenge(Base):
    __tablename__ = "challenges"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    challenge_type = Column(String(100))
    target_value = Column(Float)
    points_reward = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, server_default=func.now())

class UserAction(Base):
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255))
    building_id = Column(Integer)
    action_type = Column(String(100))
    description = Column(Text)
    points_earned = Column(Integer, default=0)
    challenge_id = Column(Integer)
    timestamp = Column(DateTime, server_default=func.now())
    energy_savings_kwh = Column(Float)
    cost_savings_usd = Column(Float)