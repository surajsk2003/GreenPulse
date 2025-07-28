import numpy as np
import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
from prophet.diagnostics import cross_validation, performance_metrics
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnergyForecaster:
    def __init__(self, 
                 seasonality_mode: str = 'multiplicative',
                 changepoint_prior_scale: float = 0.05,
                 seasonality_prior_scale: float = 0.1):
        """
        Initialize the energy forecaster using Prophet
        
        Args:
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Controls flexibility of trend changes
            seasonality_prior_scale: Controls flexibility of seasonality
        """
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Usually not enough data for yearly
            seasonality_mode=seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            holidays_prior_scale=0.1,
            interval_width=0.95
        )
        
        self.is_fitted = False
        self.model_metrics = {}
        self.building_id = None
        
    def prepare_data(self, df: pd.DataFrame, building_id: Optional[int] = None) -> pd.DataFrame:
        """
        Prepare data for Prophet forecasting
        
        Args:
            df: DataFrame with energy readings
            building_id: Optional building ID to filter data
            
        Returns:
            DataFrame formatted for Prophet (ds, y columns)
        """
        logger.info("🔧 Preparing data for energy forecasting...")
        
        if building_id is not None:
            df = df[df['building_id'] == building_id].copy()
            self.building_id = building_id
            logger.info(f"🏢 Using data for building {building_id}: {len(df)} records")
        
        if len(df) < 100:
            raise ValueError(f"Insufficient data for forecasting: {len(df)} records (minimum 100 required)")
        
        # Prepare Prophet format
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(df['timestamp']),
            'y': df['meter_reading']
        })
        
        # Remove any duplicates and sort
        prophet_df = prophet_df.drop_duplicates(subset=['ds']).sort_values('ds')
        
        # Handle missing values
        prophet_df['y'] = prophet_df['y'].fillna(prophet_df['y'].median())
        
        # Add external regressors if available
        if 'air_temperature' in df.columns:
            temp_data = df.set_index('timestamp')['air_temperature'].reindex(
                prophet_df.set_index('ds').index
            ).fillna(method='forward').fillna(method='backward')
            prophet_df['temperature'] = temp_data.values
            
        if 'is_weekend' in df.columns or 'day_of_week' in df.columns:
            if 'is_weekend' in df.columns:
                weekend_data = df.set_index('timestamp')['is_weekend']
            else:
                weekend_data = (pd.to_datetime(df['timestamp']).dt.dayofweek >= 5).astype(int)
                weekend_data.index = df['timestamp']
            
            weekend_reindexed = weekend_data.reindex(
                prophet_df.set_index('ds').index
            ).fillna(0)
            prophet_df['is_weekend'] = weekend_reindexed.values
        else:
            # Calculate is_weekend from ds
            prophet_df['is_weekend'] = (prophet_df['ds'].dt.dayofweek >= 5).astype(int)
        
        logger.info(f"📊 Prepared {len(prophet_df)} data points for forecasting")
        
        return prophet_df.dropna()
    
    def add_custom_seasonalities(self):
        """Add custom seasonalities for energy consumption patterns"""
        
        # Add business hours seasonality (stronger on weekdays)
        self.model.add_seasonality(
            name='business_hours',
            period=24,
            fourier_order=8,
            condition_name='is_business_day'
        )
        
        # Add weekend seasonality
        self.model.add_seasonality(
            name='weekend',
            period=24,
            fourier_order=5,
            condition_name='is_weekend'
        )
    
    def fit(self, df: pd.DataFrame, building_id: Optional[int] = None) -> Dict[str, float]:
        """
        Train the forecasting model
        
        Args:
            df: DataFrame with energy readings
            building_id: Optional building ID to filter data
            
        Returns:
            Dictionary with training metrics
        """
        logger.info("🚀 Training energy forecasting model...")
        
        # Prepare data
        prophet_data = self.prepare_data(df, building_id)
        
        if len(prophet_data) < 100:
            raise ValueError(f"Insufficient data after preparation: {len(prophet_data)} records")
        
        # Add regressors
        if 'temperature' in prophet_data.columns:
            self.model.add_regressor('temperature', standardize=True)
            logger.info("🌡️ Added temperature as regressor")
        
        if 'is_weekend' in prophet_data.columns:
            self.model.add_regressor('is_weekend')
            logger.info("📅 Added weekend indicator as regressor")
        
        # Add business day indicator for conditional seasonality
        prophet_data['is_business_day'] = (~prophet_data['is_weekend'].astype(bool)).astype(int)
        
        # Add custom seasonalities
        try:
            self.add_custom_seasonalities()
            logger.info("📈 Added custom seasonalities")
        except Exception as e:
            logger.warning(f"Could not add custom seasonalities: {e}")
        
        # Fit model
        logger.info("🤖 Training Prophet model...")
        self.model.fit(prophet_data)
        self.is_fitted = True
        
        # Calculate training metrics using cross-validation
        try:
            metrics = self._calculate_cv_metrics(prophet_data)
            self.model_metrics = metrics
            logger.info("✅ Model training completed!")
            logger.info(f"📈 Cross-validation metrics: {metrics}")
        except Exception as e:
            logger.warning(f"Could not calculate cross-validation metrics: {e}")
            self.model_metrics = {
                'training_samples': len(prophet_data),
                'data_range_days': (prophet_data['ds'].max() - prophet_data['ds'].min()).days,
                'avg_energy_usage': prophet_data['y'].mean(),
                'energy_std': prophet_data['y'].std()
            }
        
        return self.model_metrics
    
    def forecast(self, periods: int = 24, freq: str = 'H') -> Dict[str, any]:
        """
        Generate energy consumption forecast
        
        Args:
            periods: Number of periods to forecast
            freq: Frequency of forecast ('H' for hourly, 'D' for daily)
            
        Returns:
            Dictionary with forecast data and metadata
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making forecasts")
        
        logger.info(f"🔮 Generating {periods} period forecast...")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        
        # Add regressor values for future periods
        if 'temperature' in self.model.extra_regressors:
            # Use seasonal temperature pattern (simplified)
            future_temps = self._generate_future_temperatures(future, periods)
            future['temperature'] = future_temps
        
        if 'is_weekend' in self.model.extra_regressors:
            future['is_weekend'] = (future['ds'].dt.dayofweek >= 5).astype(int)
        
        # Add business day indicator
        if 'is_weekend' in future.columns:
            future['is_business_day'] = (~future['is_weekend'].astype(bool)).astype(int)
        
        # Generate forecast
        forecast = self.model.predict(future)
        
        # Extract forecast for requested periods
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        
        # Calculate additional metrics
        total_predicted = forecast_data['yhat'].sum()
        confidence_width = (forecast_data['yhat_upper'] - forecast_data['yhat_lower']).mean()
        trend_analysis = self._analyze_forecast_trend(forecast_data)
        
        result = {
            'building_id': self.building_id,
            'forecast_period': periods,
            'forecast_frequency': freq,
            'forecast': [
                {
                    'timestamp': row['ds'].isoformat(),
                    'predicted_kwh': float(row['yhat']),
                    'confidence_lower': float(row['yhat_lower']),
                    'confidence_upper': float(row['yhat_upper']),
                    'confidence_level': 0.95
                }
                for _, row in forecast_data.iterrows()
            ],
            'summary': {
                'total_predicted_kwh': float(total_predicted),
                'average_hourly_kwh': float(total_predicted / periods) if periods > 0 else 0,
                'confidence_interval_width': float(confidence_width),
                'trend': trend_analysis,
                'peak_predicted_hour': forecast_data.loc[forecast_data['yhat'].idxmax(), 'ds'].strftime('%H:%M'),
                'min_predicted_hour': forecast_data.loc[forecast_data['yhat'].idxmin(), 'ds'].strftime('%H:%M')
            },
            'model_info': {
                'type': 'Prophet',
                'seasonalities': list(self.model.seasonalities.keys()),
                'regressors': list(self.model.extra_regressors.keys()),
                'training_metrics': self.model_metrics
            }
        }
        
        logger.info(f"✅ Forecast generated: {periods} periods, trend: {trend_analysis}")
        
        return result
    
    def _generate_future_temperatures(self, future_df: pd.DataFrame, periods: int) -> np.ndarray:
        """Generate realistic future temperatures based on seasonal patterns"""
        
        # Simple seasonal temperature model
        base_temp = 70  # Base temperature in Fahrenheit
        
        # Create seasonal pattern
        day_of_year = future_df['ds'].dt.dayofyear
        seasonal_temp = base_temp + 20 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Add daily variation
        hour_of_day = future_df['ds'].dt.hour
        daily_temp = 5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        
        # Add some randomness for the future periods
        future_temps = seasonal_temp + daily_temp
        if periods > 0:
            future_temps.iloc[-periods:] += np.random.normal(0, 2, periods)
        
        return future_temps.values
    
    def _analyze_forecast_trend(self, forecast_data: pd.DataFrame) -> str:
        """Analyze the trend in forecast data"""
        
        if len(forecast_data) < 2:
            return "insufficient_data"
        
        first_half = forecast_data['yhat'].iloc[:len(forecast_data)//2].mean()
        second_half = forecast_data['yhat'].iloc[len(forecast_data)//2:].mean()
        
        change_percent = ((second_half - first_half) / first_half) * 100 if first_half != 0 else 0
        
        if change_percent > 5:
            return f"increasing ({change_percent:.1f}% higher)"
        elif change_percent < -5:
            return f"decreasing ({abs(change_percent):.1f}% lower)"
        else:
            return "stable"
    
    def _calculate_cv_metrics(self, data: pd.DataFrame, 
                             initial: str = '30 days', 
                             period: str = '7 days', 
                             horizon: str = '24 hours') -> Dict[str, float]:
        """Calculate cross-validation metrics"""
        
        # Only perform CV if we have enough data
        if len(data) < 100:
            raise ValueError("Insufficient data for cross-validation")
        
        logger.info("📊 Performing cross-validation...")
        
        # Perform cross-validation
        cv_results = cross_validation(
            self.model, 
            initial=initial, 
            period=period, 
            horizon=horizon,
            parallel='processes'
        )
        
        # Calculate performance metrics
        metrics_df = performance_metrics(cv_results)
        
        return {
            'mape': float(metrics_df['mape'].mean()),
            'mae': float(metrics_df['mae'].mean()),
            'rmse': float(metrics_df['rmse'].mean()),
            'coverage': float(metrics_df['coverage'].mean()),
            'cv_folds': len(cv_results['cutoff'].unique()),
            'training_samples': len(data)
        }
    
    def get_forecast_components(self) -> Dict[str, any]:
        """Get forecast components (trend, seasonality, etc.)"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted to get components")
        
        # Create a future dataframe for component analysis
        future = self.model.make_future_dataframe(periods=24, freq='H')
        
        # Add regressors
        if 'temperature' in self.model.extra_regressors:
            future['temperature'] = self._generate_future_temperatures(future, 24)
        
        if 'is_weekend' in self.model.extra_regressors:
            future['is_weekend'] = (future['ds'].dt.dayofweek >= 5).astype(int)
        
        if 'is_weekend' in future.columns:
            future['is_business_day'] = (~future['is_weekend'].astype(bool)).astype(int)
        
        # Generate forecast with components
        forecast = self.model.predict(future)
        
        components = {
            'trend': forecast[['ds', 'trend']].tail(24).to_dict('records'),
            'daily': forecast[['ds', 'daily']].tail(24).to_dict('records') if 'daily' in forecast.columns else [],
            'weekly': forecast[['ds', 'weekly']].tail(24).to_dict('records') if 'weekly' in forecast.columns else []
        }
        
        return components

def main():
    """Example usage of the energy forecaster"""
    
    logger.info("🌱 GreenPulse Energy Forecasting Demo")
    
    # Create sample data for demonstration
    dates = pd.date_range('2024-01-01', periods=2000, freq='H')
    np.random.seed(42)
    
    # Generate realistic energy consumption pattern
    base_consumption = 100
    
    # Daily pattern (higher during day, lower at night)
    hourly_pattern = 30 * np.sin(2 * np.pi * (np.arange(len(dates)) % 24 - 6) / 24)
    hourly_pattern = np.maximum(hourly_pattern, -20)  # Don't go too negative
    
    # Weekly pattern (lower on weekends)
    daily_component = np.arange(len(dates)) // 24
    weekend_mask = (daily_component % 7) >= 5
    weekly_pattern = np.where(weekend_mask, -15, 0)
    
    # Temperature effect
    temperatures = 70 + 20 * np.sin(2 * np.pi * (np.arange(len(dates)) / 24 - 80) / 365)
    temp_effect = 0.5 * (temperatures - 70)  # Energy increases with extreme temperatures
    
    # Random noise
    noise = np.random.normal(0, 5, len(dates))
    
    # Combine all components
    meter_readings = base_consumption + hourly_pattern + weekly_pattern + temp_effect + noise
    meter_readings = np.maximum(meter_readings, 10)  # Minimum consumption
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'building_id': 1,
        'meter_reading': meter_readings,
        'air_temperature': temperatures,
        'is_weekend': weekend_mask
    })
    
    # Initialize and train forecaster
    forecaster = EnergyForecaster()
    
    # Split data
    train_data = sample_data[:-48]  # All but last 48 hours
    test_data = sample_data[-48:]   # Last 48 hours for validation
    
    # Train model
    metrics = forecaster.fit(train_data, building_id=1)
    
    # Generate forecast
    forecast_result = forecaster.forecast(periods=24, freq='H')
    
    logger.info("🎉 Energy forecasting demo completed!")
    logger.info(f"📊 Forecast summary: {forecast_result['summary']}")
    
    return forecaster, forecast_result

if __name__ == "__main__":
    forecaster, forecast_result = main()