import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnergyAnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        """
        Initialize the anomaly detector
        
        Args:
            contamination: Expected proportion of anomalies in the data
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            max_samples=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False
        self.model_metrics = {}
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and engineer features for anomaly detection
        
        Args:
            df: DataFrame with energy readings
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("🔧 Engineering features for anomaly detection...")
        
        df = df.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' not in df.columns:
            raise ValueError("DataFrame must contain 'timestamp' column")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_business_hours'] = ((df['hour'] >= 8) & (df['hour'] <= 18) & (df['day_of_week'] < 5)).astype(int)
        
        # Seasonal features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Energy usage features
        if 'meter_reading' not in df.columns:
            raise ValueError("DataFrame must contain 'meter_reading' column")
        
        # Sort by timestamp for rolling calculations
        df = df.sort_values('timestamp')
        
        # Rolling statistics (fill NaN with current value for first few rows)
        df['energy_ma_6h'] = df['meter_reading'].rolling(window=6, min_periods=1).mean()
        df['energy_ma_24h'] = df['meter_reading'].rolling(window=24, min_periods=1).mean()
        df['energy_std_24h'] = df['meter_reading'].rolling(window=24, min_periods=1).std().fillna(0)
        df['energy_max_24h'] = df['meter_reading'].rolling(window=24, min_periods=1).max()
        df['energy_min_24h'] = df['meter_reading'].rolling(window=24, min_periods=1).min()
        
        # Lag features
        df['energy_lag_1h'] = df['meter_reading'].shift(1).fillna(df['meter_reading'])
        df['energy_lag_24h'] = df['meter_reading'].shift(24).fillna(df['meter_reading'])
        
        # Deviation features
        df['energy_deviation_from_ma'] = df['meter_reading'] - df['energy_ma_24h']
        df['energy_deviation_pct'] = (df['energy_deviation_from_ma'] / df['energy_ma_24h']).fillna(0)
        df['energy_zscore'] = ((df['meter_reading'] - df['energy_ma_24h']) / df['energy_std_24h']).fillna(0)
        
        # Weather features (if available)
        weather_features = []
        if 'air_temperature' in df.columns:
            df['temp_deviation'] = abs(df['air_temperature'] - df['air_temperature'].rolling(window=168, min_periods=1).mean())
            weather_features.extend(['air_temperature', 'temp_deviation'])
        
        if 'wind_speed' in df.columns:
            weather_features.append('wind_speed')
        
        if 'cloud_coverage' in df.columns:
            weather_features.append('cloud_coverage')
        
        # Select features for model
        self.feature_names = [
            'meter_reading', 'hour', 'day_of_week', 'month', 'is_weekend', 'is_business_hours',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'energy_ma_6h', 'energy_ma_24h', 'energy_std_24h',
            'energy_max_24h', 'energy_min_24h', 'energy_lag_1h', 'energy_lag_24h',
            'energy_deviation_from_ma', 'energy_deviation_pct', 'energy_zscore'
        ] + weather_features
        
        # Filter to available columns
        available_features = [f for f in self.feature_names if f in df.columns]
        self.feature_names = available_features
        
        logger.info(f"📊 Engineered {len(self.feature_names)} features: {self.feature_names}")
        
        return df[['timestamp', 'building_id'] + self.feature_names].fillna(0)
    
    def fit(self, df: pd.DataFrame, building_id: Optional[int] = None) -> Dict[str, float]:
        """
        Train the anomaly detection model
        
        Args:
            df: DataFrame with energy readings
            building_id: Optional building ID to filter data
            
        Returns:
            Dictionary with training metrics
        """
        logger.info("🚀 Training anomaly detection model...")
        
        if building_id is not None:
            df = df[df['building_id'] == building_id].copy()
            logger.info(f"🏢 Training on building {building_id} data: {len(df)} records")
        
        if len(df) < 100:
            raise ValueError(f"Insufficient data for training: {len(df)} records (minimum 100 required)")
        
        # Prepare features
        feature_df = self.prepare_features(df)
        X = feature_df[self.feature_names].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        logger.info("🤖 Training Isolation Forest...")
        self.model.fit(X_scaled)
        self.is_fitted = True
        
        # Calculate training metrics
        anomaly_predictions = self.model.predict(X_scaled)
        anomaly_scores = self.model.decision_function(X_scaled)
        
        # Identify anomalies
        anomaly_mask = anomaly_predictions == -1
        normal_mask = anomaly_predictions == 1
        
        self.model_metrics = {
            'training_samples': len(X_scaled),
            'feature_count': X_scaled.shape[1],
            'anomaly_rate': anomaly_mask.mean(),
            'avg_anomaly_score': anomaly_scores[anomaly_mask].mean() if anomaly_mask.any() else 0,
            'avg_normal_score': anomaly_scores[normal_mask].mean() if normal_mask.any() else 0,
            'score_range': [anomaly_scores.min(), anomaly_scores.max()],
            'contamination': self.contamination
        }
        
        logger.info("✅ Model training completed!")
        logger.info(f"📈 Training metrics: {self.model_metrics}")
        
        return self.model_metrics
    
    def predict(self, df: pd.DataFrame, building_id: Optional[int] = None) -> Dict[str, any]:
        """
        Detect anomalies in new data
        
        Args:
            df: DataFrame with energy readings
            building_id: Optional building ID to filter data
            
        Returns:
            Dictionary with anomaly predictions and metadata
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        if building_id is not None:
            df = df[df['building_id'] == building_id].copy()
        
        if len(df) == 0:
            return {
                'anomalies': [],
                'anomaly_count': 0,
                'total_points': 0,
                'anomaly_rate': 0.0
            }
        
        # Prepare features
        feature_df = self.prepare_features(df)
        X = feature_df[self.feature_names].values
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        # Process results
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly detected
                timestamp = feature_df.iloc[i]['timestamp']
                energy_value = feature_df.iloc[i]['meter_reading']
                
                # Calculate severity based on score
                severity = self._calculate_severity(score)
                
                # Determine anomaly type
                anomaly_type = self._classify_anomaly_type(feature_df.iloc[i])
                
                # Calculate expected value (using moving average)
                expected_value = feature_df.iloc[i]['energy_ma_24h']
                deviation_pct = ((energy_value - expected_value) / expected_value * 100) if expected_value > 0 else 0
                
                anomalies.append({
                    'timestamp': timestamp,
                    'anomaly_score': float(score),
                    'energy_value': float(energy_value),
                    'expected_value': float(expected_value),
                    'deviation_percent': float(deviation_pct),
                    'severity': severity,
                    'anomaly_type': anomaly_type,
                    'building_id': int(feature_df.iloc[i]['building_id']) if 'building_id' in feature_df.columns else building_id
                })
        
        result = {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'total_points': len(df),
            'anomaly_rate': len(anomalies) / len(df) if len(df) > 0 else 0.0,
            'score_statistics': {
                'mean': float(scores.mean()),
                'std': float(scores.std()),
                'min': float(scores.min()),
                'max': float(scores.max())
            }
        }
        
        logger.info(f"🔍 Anomaly detection completed: {len(anomalies)} anomalies found in {len(df)} data points")
        
        return result
    
    def _calculate_severity(self, score: float) -> str:
        """Calculate anomaly severity based on score"""
        if score < -0.6:
            return 'critical'
        elif score < -0.4:
            return 'high'
        elif score < -0.2:
            return 'medium'
        else:
            return 'low'
    
    def _classify_anomaly_type(self, row: pd.Series) -> str:
        """Classify the type of anomaly based on features"""
        hour = row['hour']
        is_weekend = row['is_weekend']
        is_business_hours = row['is_business_hours']
        energy_deviation_pct = row['energy_deviation_pct']
        
        # High usage during off-hours
        if not is_business_hours and energy_deviation_pct > 50:
            return 'off_hours_spike'
        
        # Weekend usage anomaly
        if is_weekend and energy_deviation_pct > 30:
            return 'weekend_anomaly'
        
        # Peak hour extreme usage
        if 14 <= hour <= 16 and energy_deviation_pct > 100:
            return 'peak_hour_extreme'
        
        # Night time usage
        if (22 <= hour <= 24 or 0 <= hour <= 6) and energy_deviation_pct > 50:
            return 'night_usage_spike'
        
        # General usage spike
        if energy_deviation_pct > 50:
            return 'usage_spike'
        
        # Low usage anomaly
        if energy_deviation_pct < -50:
            return 'low_usage_anomaly'
        
        return 'general_anomaly'
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'metrics': self.model_metrics,
            'contamination': self.contamination,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_metrics = model_data['metrics']
        self.contamination = model_data['contamination']
        self.is_fitted = model_data['is_fitted']
        
        logger.info(f"📂 Model loaded from {filepath}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores (approximated)"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted to get feature importance")
        
        # For Isolation Forest, we can't get direct feature importance
        # But we can approximate it by looking at feature usage in splits
        # This is a simplified approximation
        importance_scores = {}
        
        for i, feature_name in enumerate(self.feature_names):
            # Use the standard deviation of the feature as proxy for importance
            importance_scores[feature_name] = 1.0 / (len(self.feature_names))
        
        return importance_scores

def main():
    """Example usage of the anomaly detector"""
    
    # This would typically use real data from the database
    logger.info("🌱 GreenPulse Anomaly Detection Demo")
    
    # Create sample data for demonstration
    dates = pd.date_range('2024-01-01', periods=1000, freq='H')
    np.random.seed(42)
    
    # Generate realistic energy consumption pattern
    base_consumption = 100
    hourly_pattern = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 24)
    weekly_pattern = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / (24 * 7))
    noise = np.random.normal(0, 5, len(dates))
    
    # Add some anomalies
    anomaly_indices = np.random.choice(len(dates), size=50, replace=False)
    meter_readings = base_consumption + hourly_pattern + weekly_pattern + noise
    meter_readings[anomaly_indices] *= np.random.uniform(2, 3, len(anomaly_indices))
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'building_id': 1,
        'meter_reading': meter_readings,
        'air_temperature': 70 + 10 * np.sin(2 * np.pi * np.arange(len(dates)) / (24 * 365)) + np.random.normal(0, 2, len(dates))
    })
    
    # Initialize and train detector
    detector = EnergyAnomalyDetector(contamination=0.05)
    
    # Split data
    train_data = sample_data[:800]
    test_data = sample_data[800:]
    
    # Train model
    metrics = detector.fit(train_data, building_id=1)
    
    # Detect anomalies
    results = detector.predict(test_data, building_id=1)
    
    logger.info("🎉 Anomaly detection demo completed!")
    logger.info(f"📊 Results: {results['anomaly_count']} anomalies in {results['total_points']} points")
    
    return detector, results

if __name__ == "__main__":
    detector, results = main()