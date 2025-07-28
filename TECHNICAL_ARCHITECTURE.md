# GreenPulse: Technical Architecture

## 🏗️ **System Architecture Overview**

```
                    ┌─────────────────┐
                    │   Frontend      │
                    │   (Angular)     │
                    └─────────┬───────┘
                              │ HTTP/WebSocket
                    ┌─────────▼───────┐
                    │   API Gateway   │
                    │   (FastAPI)     │
                    └─────────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼─────┐ ┌──────▼──────┐ ┌─────▼─────┐
    │   ML Engine   │ │   Cache     │ │ Database  │
    │  (scikit-learn│ │  (Redis)    │ │(PostgreSQL│
    │   + Prophet)  │ │             │ │+ TimescaleDB)
    └───────────────┘ └─────────────┘ └───────────┘
              │                               │
    ┌─────────▼─────┐                ┌──────▼──────┐
    │ Model Storage │                │ Data Pipeline│
    │   (MLflow)    │                │   (ETL)     │
    └───────────────┘                └─────────────┘
```

## 🗄️ **Database Design**

### **Core Tables Schema**
```sql
-- Campus and Building Management
CREATE TABLE campuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    total_area_sqft INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    campus_id INTEGER REFERENCES campuses(id),
    name VARCHAR(255) NOT NULL,
    building_type VARCHAR(100), -- 'academic', 'residential', 'administrative', 'research'
    area_sqft INTEGER,
    floors INTEGER,
    occupancy_capacity INTEGER,
    year_built INTEGER,
    energy_star_rating INTEGER CHECK (energy_star_rating BETWEEN 1 AND 100),
    baseline_consumption_kwh FLOAT, -- Historical average for comparison
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Time-series Energy Data (Hypertable)
CREATE TABLE energy_readings (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    -- Energy meters
    electricity_kwh FLOAT DEFAULT 0,
    natural_gas_therms FLOAT DEFAULT 0,
    chilled_water_tons FLOAT DEFAULT 0,
    steam_lbs FLOAT DEFAULT 0,
    hot_water_gal FLOAT DEFAULT 0,
    -- Environmental data
    outdoor_temp_f FLOAT,
    outdoor_humidity_percent FLOAT,
    indoor_temp_f FLOAT,
    indoor_humidity_percent FLOAT,
    -- Calculated fields
    total_energy_btu FLOAT, -- Normalized energy consumption
    cost_usd FLOAT,
    carbon_emissions_lbs FLOAT,
    -- Data quality
    data_quality_score FLOAT DEFAULT 1.0, -- 0-1 score for data reliability
    meter_status VARCHAR(20) DEFAULT 'active', -- 'active', 'maintenance', 'error'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable for time-series optimization
SELECT create_hypertable('energy_readings', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for common queries
CREATE INDEX idx_energy_readings_building_time ON energy_readings (building_id, timestamp DESC);
CREATE INDEX idx_energy_readings_timestamp ON energy_readings (timestamp DESC);

-- Departments and Users
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    campus_id INTEGER REFERENCES campuses(id),
    name VARCHAR(255) NOT NULL,
    building_ids INTEGER[], -- Array of building IDs this department occupies
    head_of_department VARCHAR(255),
    contact_email VARCHAR(255),
    energy_budget_annual FLOAT, -- Annual energy budget in USD
    reduction_target_percent FLOAT DEFAULT 10.0, -- Target reduction percentage
    current_score INTEGER DEFAULT 0, -- Gamification score
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL, -- External user ID (from SSO)
    name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(50), -- 'admin', 'manager', 'user', 'viewer'
    department_id INTEGER REFERENCES departments(id),
    building_access INTEGER[], -- Array of building IDs user can access
    notification_preferences JSONB DEFAULT '{"email": true, "push": false}',
    total_points INTEGER DEFAULT 0, -- Gamification points
    created_at TIMESTAMP DEFAULT NOW()
);

-- ML Models and Predictions
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100), -- 'anomaly_detection', 'forecasting', 'classification'
    building_id INTEGER REFERENCES buildings(id),
    model_version VARCHAR(50),
    model_parameters JSONB,
    training_data_start TIMESTAMP,
    training_data_end TIMESTAMP,
    accuracy_score FLOAT,
    status VARCHAR(50) DEFAULT 'active', -- 'training', 'active', 'deprecated'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) NOT NULL,
    model_id INTEGER REFERENCES ml_models(id),
    timestamp TIMESTAMP NOT NULL,
    anomaly_score FLOAT NOT NULL, -- -1 to 1, where < 0 indicates anomaly
    anomaly_type VARCHAR(100), -- 'usage_spike', 'equipment_failure', 'schedule_deviation'
    energy_value FLOAT,
    expected_value FLOAT,
    deviation_percent FLOAT,
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'acknowledged', 'investigating', 'resolved'
    investigation_notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) NOT NULL,
    model_id INTEGER REFERENCES ml_models(id),
    forecast_timestamp TIMESTAMP NOT NULL, -- When the forecast is for
    generated_at TIMESTAMP DEFAULT NOW(), -- When the forecast was generated
    forecast_type VARCHAR(50), -- 'hourly', 'daily', 'weekly', 'monthly'
    predicted_kwh FLOAT,
    confidence_lower FLOAT,
    confidence_upper FLOAT,
    confidence_level FLOAT DEFAULT 0.95, -- 95% confidence interval
    actual_kwh FLOAT, -- Filled in after the fact for accuracy tracking
    accuracy_error FLOAT -- |predicted - actual| / actual
);

-- Insights and Recommendations
CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) NOT NULL,
    insight_type VARCHAR(100), -- 'peak_usage', 'weekend_waste', 'hvac_efficiency', 'equipment_schedule'
    priority FLOAT NOT NULL, -- 0-1 priority score
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recommendation TEXT,
    potential_savings_usd FLOAT,
    potential_savings_kwh FLOAT,
    confidence_score FLOAT, -- How confident we are in this insight
    actionable_steps JSONB, -- Array of specific actions to take
    category VARCHAR(100), -- 'immediate', 'short_term', 'long_term'
    status VARCHAR(50) DEFAULT 'new', -- 'new', 'acknowledged', 'implementing', 'completed', 'dismissed'
    implemented_at TIMESTAMP,
    actual_savings_usd FLOAT, -- Measured after implementation
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP -- Some insights may become irrelevant
);

-- Gamification and Challenges
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    challenge_type VARCHAR(100), -- 'energy_reduction', 'efficiency_improvement', 'consistency'
    target_metric VARCHAR(100), -- 'kwh_reduction', 'efficiency_score', 'usage_consistency'
    target_value FLOAT,
    points_reward INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    eligible_departments INTEGER[], -- Array of department IDs
    eligible_buildings INTEGER[], -- Array of building IDs
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_actions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    building_id INTEGER REFERENCES buildings(id),
    action_type VARCHAR(100), -- 'report_issue', 'implement_recommendation', 'schedule_maintenance'
    description TEXT,
    points_earned INTEGER DEFAULT 0,
    challenge_id INTEGER REFERENCES challenges(id), -- If part of a challenge
    timestamp TIMESTAMP DEFAULT NOW(),
    impact_measured BOOLEAN DEFAULT FALSE,
    energy_savings_kwh FLOAT, -- Measured impact
    cost_savings_usd FLOAT
);

CREATE TABLE leaderboards (
    id SERIAL PRIMARY KEY,
    period_type VARCHAR(50), -- 'daily', 'weekly', 'monthly', 'yearly'
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    entity_type VARCHAR(50), -- 'department', 'building', 'user'
    entity_id INTEGER,
    metric_type VARCHAR(100), -- 'energy_reduction', 'efficiency_score', 'points'
    metric_value FLOAT,
    rank INTEGER,
    total_participants INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts and Notifications
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id),
    user_id VARCHAR(255) REFERENCES users(user_id),
    rule_name VARCHAR(255),
    condition_type VARCHAR(100), -- 'threshold_exceeded', 'anomaly_detected', 'forecast_high'
    threshold_value FLOAT,
    comparison_operator VARCHAR(10), -- '>', '<', '>=', '<=', '=='
    metric VARCHAR(100), -- 'electricity_kwh', 'total_energy_btu', 'cost_usd'
    time_window_minutes INTEGER DEFAULT 60, -- How long condition must persist
    notification_channels JSONB DEFAULT '["email"]', -- email, sms, push, slack
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id),
    notification_type VARCHAR(100), -- 'alert', 'insight', 'challenge', 'achievement'
    title VARCHAR(255),
    message TEXT,
    data JSONB, -- Additional structured data
    channels VARCHAR(50)[], -- Which channels were used
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP
);

-- Reporting and Analytics
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(100), -- 'energy_summary', 'efficiency_analysis', 'cost_analysis'
    scope_type VARCHAR(50), -- 'building', 'department', 'campus'
    scope_id INTEGER, -- ID of the building/department/campus
    time_period_start TIMESTAMP,
    time_period_end TIMESTAMP,
    generated_by VARCHAR(255) REFERENCES users(user_id),
    report_data JSONB, -- Structured report data
    file_path VARCHAR(500), -- Path to generated PDF/Excel file
    is_scheduled BOOLEAN DEFAULT FALSE,
    schedule_cron VARCHAR(100), -- Cron expression for scheduled reports
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data Sources and Integration
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255), -- 'BMS_System_A', 'Smart_Meter_B', 'Weather_API'
    source_type VARCHAR(100), -- 'bms', 'smart_meter', 'weather', 'manual'
    building_id INTEGER REFERENCES buildings(id),
    connection_details JSONB, -- API endpoints, credentials, etc.
    data_mapping JSONB, -- How to map source data to our schema
    last_sync TIMESTAMP,
    sync_frequency_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Data Retention and Partitioning**
```sql
-- TimescaleDB automatic data retention
SELECT add_retention_policy('energy_readings', INTERVAL '2 years');

-- Continuous aggregates for performance
CREATE MATERIALIZED VIEW energy_hourly
WITH (timescaledb.continuous) AS
SELECT 
    building_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(electricity_kwh) as avg_electricity_kwh,
    MAX(electricity_kwh) as max_electricity_kwh,
    MIN(electricity_kwh) as min_electricity_kwh,
    SUM(electricity_kwh) as total_electricity_kwh,
    COUNT(*) as reading_count
FROM energy_readings
GROUP BY building_id, hour;

CREATE MATERIALIZED VIEW energy_daily
WITH (timescaledb.continuous) AS
SELECT 
    building_id,
    time_bucket('1 day', timestamp) AS day,
    AVG(electricity_kwh) as avg_electricity_kwh,
    SUM(electricity_kwh) as total_electricity_kwh,
    AVG(total_energy_btu) as avg_total_energy_btu,
    SUM(cost_usd) as total_cost_usd,
    SUM(carbon_emissions_lbs) as total_carbon_emissions_lbs
FROM energy_readings
GROUP BY building_id, day;
```

## 🤖 **ML Pipeline Architecture**

### **Model Management System**
```python
# ml_models/model_manager.py
import joblib
import mlflow
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

class ModelManager:
    def __init__(self):
        self.models = {}
        self.model_registry = {}
        
    def register_model(self, model_name: str, model_type: str, building_id: int):
        """Register a new model in the system"""
        model_id = f"{model_type}_{building_id}_{int(datetime.now().timestamp())}"
        
        self.model_registry[model_id] = {
            'name': model_name,
            'type': model_type,
            'building_id': building_id,
            'created_at': datetime.now(),
            'status': 'training'
        }
        
        return model_id
    
    def save_model(self, model_id: str, model, metrics: Dict[str, float]):
        """Save trained model with MLflow tracking"""
        with mlflow.start_run():
            # Log parameters and metrics
            mlflow.log_metrics(metrics)
            
            # Save model
            model_path = f"models/{model_id}"
            joblib.dump(model, f"{model_path}.joblib")
            mlflow.sklearn.log_model(model, "model")
            
            # Update registry
            self.model_registry[model_id].update({
                'metrics': metrics,
                'model_path': model_path,
                'status': 'active'
            })
            
            # Store in database
            self._save_to_database(model_id, metrics)
    
    def load_model(self, model_id: str):
        """Load model from storage"""
        if model_id not in self.models:
            model_path = self.model_registry[model_id]['model_path']
            self.models[model_id] = joblib.load(f"{model_path}.joblib")
        
        return self.models[model_id]
    
    def get_best_model(self, model_type: str, building_id: int) -> Optional[str]:
        """Get the best performing model for a building and type"""
        candidates = [
            (model_id, data) for model_id, data in self.model_registry.items()
            if data['type'] == model_type and data['building_id'] == building_id
        ]
        
        if not candidates:
            return None
        
        # Sort by accuracy (or appropriate metric)
        best_model = max(candidates, key=lambda x: x[1]['metrics'].get('accuracy', 0))
        return best_model[0]

# ml_models/training_pipeline.py
from sklearn.ensemble import IsolationForest
from prophet import Prophet
import pandas as pd
import numpy as np

class AnomalyDetectionPipeline:
    def __init__(self, building_id: int):
        self.building_id = building_id
        self.model = None
        self.scaler = StandardScaler()
        
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for anomaly detection"""
        df = df.copy()
        
        # Time-based features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Rolling statistics (to capture recent trends)
        df['electricity_ma_24h'] = df['electricity_kwh'].rolling('24H').mean()
        df['electricity_std_24h'] = df['electricity_kwh'].rolling('24H').std()
        
        # Weather impact (if available)
        if 'outdoor_temp_f' in df.columns:
            df['temp_deviation'] = abs(df['outdoor_temp_f'] - df['outdoor_temp_f'].rolling('7D').mean())
        
        # Occupancy proxy (for academic buildings)
        df['is_business_hours'] = ((df['hour'] >= 8) & (df['hour'] <= 18) & (df['day_of_week'] < 5)).astype(int)
        
        feature_cols = [
            'electricity_kwh', 'hour', 'day_of_week', 'month', 'is_weekend',
            'electricity_ma_24h', 'electricity_std_24h', 'is_business_hours'
        ]
        
        if 'outdoor_temp_f' in df.columns:
            feature_cols.append('temp_deviation')
        
        return df[feature_cols].fillna(method='forward').fillna(0)
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train anomaly detection model"""
        features = self.prepare_features(training_data)
        scaled_features = self.scaler.fit_transform(features)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            n_estimators=200,
            max_samples=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(scaled_features)
        
        # Calculate training metrics
        anomaly_predictions = self.model.predict(scaled_features)
        anomaly_scores = self.model.decision_function(scaled_features)
        
        metrics = {
            'anomaly_rate': (anomaly_predictions == -1).mean(),
            'avg_anomaly_score': anomaly_scores[anomaly_predictions == -1].mean(),
            'training_samples': len(scaled_features),
            'feature_count': scaled_features.shape[1]
        }
        
        return metrics
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in new data"""
        features = self.prepare_features(data)
        scaled_features = self.scaler.transform(features)
        
        predictions = self.model.predict(scaled_features)
        scores = self.model.decision_function(scaled_features)
        
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly detected
                anomalies.append({
                    'timestamp': data.iloc[i]['timestamp'],
                    'anomaly_score': score,
                    'energy_value': data.iloc[i]['electricity_kwh'],
                    'severity': self._calculate_severity(score),
                    'potential_causes': self._suggest_causes(data.iloc[i], features.iloc[i])
                })
        
        return {
            'anomaly_count': len(anomalies),
            'anomalies': anomalies,
            'overall_score': scores.mean()
        }
    
    def _calculate_severity(self, score: float) -> str:
        """Calculate anomaly severity based on score"""
        if score < -0.5:
            return 'critical'
        elif score < -0.3:
            return 'high'
        elif score < -0.1:
            return 'medium'
        else:
            return 'low'
    
    def _suggest_causes(self, data_point: pd.Series, features: pd.Series) -> list:
        """Suggest potential causes for anomaly"""
        causes = []
        
        if features['is_weekend'] and data_point['electricity_kwh'] > features['electricity_ma_24h'] * 1.5:
            causes.append("High energy usage during weekend - check for equipment left running")
        
        if not features['is_business_hours'] and data_point['electricity_kwh'] > features['electricity_ma_24h'] * 1.3:
            causes.append("High usage outside business hours - possible HVAC or lighting issues")
        
        if 'temp_deviation' in features and features['temp_deviation'] > features['temp_deviation'].quantile(0.9):
            causes.append("Extreme weather conditions may be causing higher HVAC usage")
        
        return causes or ["Unusual energy consumption pattern detected - investigate equipment status"]

class ForecastingPipeline:
    def __init__(self, building_id: int):
        self.building_id = building_id
        self.model = None
        
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet forecasting"""
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df['electricity_kwh']
        })
        
        # Add external regressors if available
        if 'outdoor_temp_f' in df.columns:
            prophet_df['temperature'] = df['outdoor_temp_f']
        
        if 'is_weekend' in df.columns:
            prophet_df['is_weekend'] = df['is_weekend']
        
        return prophet_df.dropna()
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train Prophet forecasting model"""
        prophet_data = self.prepare_data(training_data)
        
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Not enough data typically
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=0.1,
            holidays_prior_scale=0.1,
            interval_width=0.95
        )
        
        # Add regressors if available
        if 'temperature' in prophet_data.columns:
            self.model.add_regressor('temperature')
        
        if 'is_weekend' in prophet_data.columns:
            self.model.add_regressor('is_weekend')
        
        self.model.fit(prophet_data)
        
        # Calculate cross-validation metrics
        metrics = self._calculate_cv_metrics(prophet_data)
        
        return metrics
    
    def forecast(self, periods: int = 24) -> Dict[str, Any]:
        """Generate energy consumption forecast"""
        future = self.model.make_future_dataframe(periods=periods, freq='H')
        
        # Add regressor values for future periods (simplified)
        if 'temperature' in self.model.extra_regressors:
            # Use seasonal average temperature (simplified)
            future['temperature'] = 70.0  # Would be more sophisticated in production
        
        if 'is_weekend' in self.model.extra_regressors:
            future['is_weekend'] = (future['ds'].dt.dayofweek >= 5).astype(int)
        
        forecast = self.model.predict(future)
        
        # Extract forecast for requested periods
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        
        return {
            'forecast': forecast_data.to_dict('records'),
            'total_predicted_kwh': forecast_data['yhat'].sum(),
            'confidence_interval_width': (forecast_data['yhat_upper'] - forecast_data['yhat_lower']).mean(),
            'trend': self._analyze_trend(forecast_data)
        }
    
    def _calculate_cv_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate cross-validation metrics"""
        from prophet.diagnostics import cross_validation, performance_metrics
        
        # Perform cross-validation
        cv_results = cross_validation(
            self.model, 
            initial='30 days', 
            period='7 days', 
            horizon='24 hours'
        )
        
        metrics = performance_metrics(cv_results)
        
        return {
            'mape': metrics['mape'].mean(),
            'mae': metrics['mae'].mean(),
            'rmse': metrics['rmse'].mean(),
            'coverage': metrics['coverage'].mean()
        }
    
    def _analyze_trend(self, forecast_data: pd.DataFrame) -> str:
        """Analyze forecast trend"""
        first_half = forecast_data['yhat'].iloc[:len(forecast_data)//2].mean()
        second_half = forecast_data['yhat'].iloc[len(forecast_data)//2:].mean()
        
        change_percent = ((second_half - first_half) / first_half) * 100
        
        if change_percent > 5:
            return f"increasing ({change_percent:.1f}% higher)"
        elif change_percent < -5:
            return f"decreasing ({abs(change_percent):.1f}% lower)"
        else:
            return "stable"
```

## 🌐 **API Architecture**

### **FastAPI Application Structure**
```python
# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

# Import routers
from app.routers import buildings, energy, analytics, gamification, alerts, insights
from app.core.config import settings
from app.core.database import engine, Base
from app.core.cache import redis_client
from app.ml.scheduler import MLScheduler

# ML scheduler instance
ml_scheduler = MLScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    ml_scheduler.start()
    yield
    # Shutdown
    ml_scheduler.stop()
    await redis_client.close()

app = FastAPI(
    title="GreenPulse API",
    description="Smart Energy Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(buildings.router, prefix="/api/buildings", tags=["buildings"])
app.include_router(energy.router, prefix="/api/energy", tags=["energy"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["gamification"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])

@app.get("/")
async def root():
    return {"message": "GreenPulse API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        from app.core.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        return {"status": "healthy", "database": "connected", "cache": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )
```

### **Key API Endpoints**
```python
# backend/app/routers/energy.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd

router = APIRouter()

@router.get("/buildings/{building_id}/current")
async def get_current_energy(
    building_id: int,
    db: Session = Depends(get_db)
):
    """Get current energy consumption for a building"""
    # Get latest reading
    latest_reading = db.query(EnergyReading)\
        .filter(EnergyReading.building_id == building_id)\
        .order_by(EnergyReading.timestamp.desc())\
        .first()
    
    if not latest_reading:
        raise HTTPException(status_code=404, detail="No energy data found")
    
    # Calculate efficiency score
    building = db.query(Building).filter(Building.id == building_id).first()
    efficiency_score = calculate_efficiency_score(latest_reading, building)
    
    return {
        "building_id": building_id,
        "timestamp": latest_reading.timestamp,
        "electricity_kwh": latest_reading.electricity_kwh,
        "total_energy_btu": latest_reading.total_energy_btu,
        "cost_usd": latest_reading.cost_usd,
        "carbon_emissions_lbs": latest_reading.carbon_emissions_lbs,
        "efficiency_score": efficiency_score,
        "status": "normal" if efficiency_score > 70 else "attention_needed"
    }

@router.get("/buildings/{building_id}/historical")
async def get_historical_energy(
    building_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    granularity: str = Query("hourly", regex="^(hourly|daily|weekly)$"),
    metrics: List[str] = Query(["electricity_kwh"]),
    db: Session = Depends(get_db)
):
    """Get historical energy data with various granularities"""
    
    cache_key = f"energy_historical_{building_id}_{start_date}_{end_date}_{granularity}"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    # Query based on granularity
    if granularity == "hourly":
        query = db.query(EnergyReading)\
            .filter(EnergyReading.building_id == building_id)\
            .filter(EnergyReading.timestamp >= start_date)\
            .filter(EnergyReading.timestamp <= end_date)\
            .order_by(EnergyReading.timestamp)
    elif granularity == "daily":
        # Use materialized view for better performance
        query = db.query(EnergyDaily)\
            .filter(EnergyDaily.building_id == building_id)\
            .filter(EnergyDaily.day >= start_date.date())\
            .filter(EnergyDaily.day <= end_date.date())\
            .order_by(EnergyDaily.day)
    
    readings = query.all()
    
    result = {
        "building_id": building_id,
        "period": {"start": start_date, "end": end_date},
        "granularity": granularity,
        "data_points": len(readings),
        "readings": [
            {
                "timestamp": r.timestamp if granularity == "hourly" else r.day,
                **{metric: getattr(r, metric, 0) for metric in metrics}
            }
            for r in readings
        ],
        "summary": calculate_period_summary(readings, metrics)
    }
    
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result, default=str))
    
    return result

@router.get("/buildings/{building_id}/comparison")
async def compare_building_energy(
    building_id: int,
    comparison_period: str = Query("last_week", regex="^(yesterday|last_week|last_month|last_year)$"),
    baseline_period: str = Query("same_period_last_year"),
    db: Session = Depends(get_db)
):
    """Compare building energy usage against historical baselines"""
    
    # Calculate date ranges
    comparison_start, comparison_end = get_period_dates(comparison_period)
    baseline_start, baseline_end = get_baseline_dates(comparison_start, comparison_end, baseline_period)
    
    # Get data for both periods
    comparison_data = get_energy_summary(db, building_id, comparison_start, comparison_end)
    baseline_data = get_energy_summary(db, building_id, baseline_start, baseline_end)
    
    # Calculate metrics
    metrics = calculate_comparison_metrics(comparison_data, baseline_data)
    
    return {
        "building_id": building_id,
        "comparison": {
            "period": comparison_period,
            "dates": {"start": comparison_start, "end": comparison_end},
            "total_kwh": comparison_data["total_kwh"],
            "avg_daily_kwh": comparison_data["avg_daily_kwh"],
            "cost_usd": comparison_data["total_cost"]
        },
        "baseline": {
            "period": baseline_period,
            "dates": {"start": baseline_start, "end": baseline_end},
            "total_kwh": baseline_data["total_kwh"],
            "avg_daily_kwh": baseline_data["avg_daily_kwh"],
            "cost_usd": baseline_data["total_cost"]
        },
        "metrics": {
            "energy_change_percent": metrics["energy_change_percent"],
            "cost_change_percent": metrics["cost_change_percent"],
            "efficiency_trend": metrics["efficiency_trend"],
            "carbon_impact_change_lbs": metrics["carbon_change_lbs"]
        },
        "insights": generate_comparison_insights(metrics)
    }

@router.post("/buildings/{building_id}/target")
async def set_energy_target(
    building_id: int,
    target: EnergyTargetCreate,
    db: Session = Depends(get_db)
):
    """Set energy reduction targets for a building"""
    
    # Validate building exists
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Create target record
    new_target = EnergyTarget(
        building_id=building_id,
        target_type=target.target_type,
        target_value=target.target_value,
        target_period=target.target_period,
        start_date=target.start_date,
        end_date=target.end_date,
        created_by=target.created_by
    )
    
    db.add(new_target)
    db.commit()
    db.refresh(new_target)
    
    return {
        "target_id": new_target.id,
        "message": f"Energy target set: {target.target_value}% reduction",
        "tracking_starts": target.start_date
    }
```

## 📊 **Frontend Architecture**

### **Angular Application Structure**
```
frontend/
├── src/
│   ├── app/
│   │   ├── core/                    # Singleton services
│   │   │   ├── auth/
│   │   │   ├── api/
│   │   │   └── cache/
│   │   ├── shared/                  # Reusable components
│   │   │   ├── components/
│   │   │   ├── pipes/
│   │   │   └── directives/
│   │   ├── features/                # Feature modules
│   │   │   ├── dashboard/
│   │   │   ├── buildings/
│   │   │   ├── analytics/
│   │   │   ├── gamification/
│   │   │   └── reports/
│   │   ├── layouts/                 # App layouts
│   │   └── app-routing.module.ts
│   ├── assets/
│   ├── environments/
│   └── styles/
```

### **Core Services**
```typescript
// src/app/core/services/energy-data.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable, timer } from 'rxjs';
import { map, shareReplay, switchMap } from 'rxjs/operators';

export interface EnergyReading {
  timestamp: string;
  electricity_kwh: number;
  total_energy_btu: number;
  cost_usd: number;
  carbon_emissions_lbs: number;
}

export interface AnomalyAlert {
  id: number;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  building_id: number;
}

@Injectable({
  providedIn: 'root'
})
export class EnergyDataService {
  private readonly apiUrl = environment.apiUrl;
  private selectedBuildingSubject = new BehaviorSubject<number>(1);
  private realTimeDataSubject = new BehaviorSubject<EnergyReading[]>([]);

  public selectedBuilding$ = this.selectedBuildingSubject.asObservable();
  public realTimeData$ = this.realTimeDataSubject.asObservable();

  constructor(private http: HttpClient) {
    this.startRealTimeUpdates();
  }

  private startRealTimeUpdates() {
    // Update every 30 seconds
    timer(0, 30000).pipe(
      switchMap(() => this.selectedBuilding$),
      switchMap(buildingId => this.getCurrentEnergy(buildingId))
    ).subscribe(data => {
      const currentData = this.realTimeDataSubject.value;
      const updatedData = [...currentData.slice(-23), data]; // Keep last 24 readings
      this.realTimeDataSubject.next(updatedData);
    });
  }

  setSelectedBuilding(buildingId: number) {
    this.selectedBuildingSubject.next(buildingId);
  }

  getBuildings(): Observable<Building[]> {
    return this.http.get<Building[]>(`${this.apiUrl}/buildings`).pipe(
      shareReplay(1)
    );
  }

  getCurrentEnergy(buildingId: number): Observable<EnergyReading> {
    return this.http.get<EnergyReading>(`${this.apiUrl}/energy/buildings/${buildingId}/current`);
  }

  getHistoricalEnergy(
    buildingId: number, 
    startDate: Date, 
    endDate: Date,
    granularity: 'hourly' | 'daily' | 'weekly' = 'hourly'
  ): Observable<EnergyReading[]> {
    const params = new HttpParams()
      .set('start_date', startDate.toISOString())
      .set('end_date', endDate.toISOString())
      .set('granularity', granularity);

    return this.http.get<{readings: EnergyReading[]}>
      (`${this.apiUrl}/energy/buildings/${buildingId}/historical`, { params })
      .pipe(map(response => response.readings));
  }

  getEnergyForecast(buildingId: number, hours: number = 24): Observable<any> {
    return this.http.get(`${this.apiUrl}/energy/buildings/${buildingId}/forecast`, {
      params: { hours: hours.toString() }
    });
  }

  getAnomalies(buildingId: number): Observable<AnomalyAlert[]> {
    return this.http.get<{anomalies: AnomalyAlert[]}>
      (`${this.apiUrl}/energy/buildings/${buildingId}/anomalies`)
      .pipe(map(response => response.anomalies));
  }

  getInsights(buildingId: number): Observable<any[]> {
    return this.http.get<{insights: any[]}>
      (`${this.apiUrl}/insights/buildings/${buildingId}`)
      .pipe(map(response => response.insights));
  }

  getEfficiencyLeaderboard(period: string = 'week'): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/gamification/leaderboard`, {
      params: { period }
    });
  }

  compareBuildings(buildingIds: number[], period: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/analytics/compare`, {
      building_ids: buildingIds,
      period: period
    });
  }
}
```

## 🚀 **Deployment Architecture**

### **Docker Configuration**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build --prod

FROM nginx:alpine
COPY --from=builder /app/dist/greenpulse-dashboard /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
```

### **Production Docker Compose**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      POSTGRES_DB: greenpulse
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - greenpulse-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - greenpulse-network
    restart: unless-stopped

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/greenpulse
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      - db
      - redis
    networks:
      - greenpulse-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - greenpulse-network
    restart: unless-stopped

  ml-worker:
    build: ./backend
    command: python -m app.ml.worker
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/greenpulse
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - db
      - redis
    networks:
      - greenpulse-network
    restart: unless-stopped
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '2'
          memory: 2G

volumes:
  postgres_data:
  redis_data:

networks:
  greenpulse-network:
    driver: bridge
```

### **Kubernetes Deployment (Optional)**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: greenpulse-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: greenpulse-backend
  template:
    metadata:
      labels:
        app: greenpulse-backend
    spec:
      containers:
      - name: backend
        image: greenpulse/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: greenpulse-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

This comprehensive technical architecture provides:

1. **Scalable Database Design** with TimescaleDB for time-series optimization
2. **Robust ML Pipeline** with model management and automated training
3. **High-Performance API** with caching and real-time capabilities  
4. **Modern Frontend** with Angular and real-time updates
5. **Production-Ready Deployment** with Docker and Kubernetes support

The architecture supports the hackathon timeline while being extensible for production use.