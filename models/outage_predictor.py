import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

class OutagePredictor:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.features = None
        self.is_trained = False
    
    def prepare_data(self, grid_data, weather_data, outage_history):
        """Prepare data for training the outage prediction model"""
        substations = grid_data['substations']
        lines = grid_data['transmission_lines']
        
        # Extract features from outage history
        data = []
        
        for _, outage in outage_history.iterrows():
            component_id = outage['component_id']
            component_type = outage['component_type']
            district = outage['district']
            date = outage['date']
            
            # Get component details
            if component_type == 'substation':
                component = substations[substations['id'] == component_id].iloc[0]
                voltage_level = component['voltage_level']
                capacity = component['capacity_mw']
                age = 2023 - component['year_commissioned']
                health_index = component['health_index']
                transformer_count = component['transformer_count']
                
                # Add substation specific features
                record = {
                    'component_id': component_id,
                    'component_type': component_type,
                    'district': district,
                    'voltage_level': voltage_level,
                    'capacity_mw': capacity,
                    'age_years': age,
                    'health_index': health_index,
                    'transformer_count': transformer_count,
                    'line_length_km': 0,  # Not applicable for substations
                    'current_load_pct': 0  # Not directly available for substations
                }
                
            else:  # transmission line
                component = lines[lines['id'] == component_id].iloc[0]
                voltage_level = component['voltage']
                capacity = component['capacity_mw']
                age = 2023 - component['year_commissioned']
                health_index = component['health_index']
                
                # Add line specific features
                record = {
                    'component_id': component_id,
                    'component_type': component_type,
                    'district': district,
                    'voltage_level': voltage_level,
                    'capacity_mw': capacity,
                    'age_years': age,
                    'health_index': health_index,
                    'transformer_count': 0,  # Not applicable for lines
                    'line_length_km': component['length_km'],
                    'current_load_pct': component['current_load_pct']
                }
            
            # Add weather data
            weather = weather_data[(weather_data['date'] == date) & (weather_data['district'] == district)]
            if not weather.empty:
                weather = weather.iloc[0]
                record.update({
                    'temperature_c': weather['temperature_c'],
                    'precipitation_mm': weather['precipitation_mm'],
                    'wind_speed_kmh': weather['wind_speed_kmh'],
                    'storm_event': weather['storm_event'],
                    'humidity_pct': weather['humidity_pct'],
                    'snow_cm': weather['snow_cm']
                })
            else:
                # If no weather data, use defaults
                record.update({
                    'temperature_c': 20,
                    'precipitation_mm': 0,
                    'wind_speed_kmh': 10,
                    'storm_event': False,
                    'humidity_pct': 50,
                    'snow_cm': 0
                })
            
            # Add cause and duration
            record['cause'] = outage['cause']
            record['duration_hours'] = outage['duration_hours']
            
            data.append(record)
        
        return pd.DataFrame(data)
    
    def train(self, grid_data, weather_data, outage_history):
        """Train the outage duration prediction model"""
        # Prepare the data
        df = self.prepare_data(grid_data, weather_data, outage_history)
        
        # Define features and target
        X = df.drop(['duration_hours', 'component_id'], axis=1)
        y = df['duration_hours']
        
        # Save the feature list for prediction
        self.features = list(X.columns)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Define preprocessing for numerical and categorical features
        numerical_features = ['capacity_mw', 'age_years', 'health_index', 'transformer_count', 
                             'line_length_km', 'current_load_pct', 'temperature_c', 
                             'precipitation_mm', 'wind_speed_kmh', 'humidity_pct', 'snow_cm']
        
        categorical_features = ['component_type', 'district', 'voltage_level', 'cause', 'storm_event']
        
        # Create preprocessors
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), numerical_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
            ])
        
        # Train the model
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            min_child_weight=1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='reg:squarederror',
            random_state=42
        )
        
        # Create pipeline
        model = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', xgb_model)
        ])
        
        # Fit the model
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Mean Squared Error: {mse:.2f}")
        print(f"Mean Absolute Error: {mae:.2f}")
        print(f"R² Score: {r2:.2f}")
        
        self.model = model
        self.preprocessor = preprocessor
        self.is_trained = True
        
        return {
            "mse": mse,
            "mae": mae,
            "r2": r2
        }
    
    def predict_outage_duration(self, features_dict):
        """Predict outage duration based on input features"""
        if not self.is_trained:
            raise ValueError("Model is not trained yet. Call train() first.")
        
        # Ensure all required features are present
        for feature in self.features:
            if feature not in features_dict and feature not in ['component_id']:
                features_dict[feature] = 0  # Default value
        
        # Create a DataFrame with the input features
        X = pd.DataFrame([features_dict])
        
        # Make prediction
        duration_hours = self.model.predict(X)[0]
        
        return max(0.5, duration_hours)  # Minimum duration of 30 minutes

    def predict_outage_probability(self, features_dict):
        """
        Estimate the probability of an outage based on the input features
        This is a simplified model using heuristics
        """
        # Base probability
        probability = 0.01
        
        # Age factor (older infrastructure = higher risk)
        if 'age_years' in features_dict:
            age = features_dict['age_years']
            probability += 0.005 * min(age / 10, 5)  # Cap at 5x increase for very old infrastructure
        
        # Health index factor (lower health = higher risk)
        if 'health_index' in features_dict:
            health = features_dict['health_index']
            probability += 0.1 * (1 - health)
        
        # Weather factors
        if 'storm_event' in features_dict and features_dict['storm_event']:
            probability += 0.2
        
        if 'precipitation_mm' in features_dict:
            precip = features_dict['precipitation_mm']
            if precip > 50:  # Heavy rain
                probability += 0.15
            elif precip > 20:  # Moderate rain
                probability += 0.05
        
        if 'wind_speed_kmh' in features_dict:
            wind = features_dict['wind_speed_kmh']
            if wind > 50:  # Very high winds
                probability += 0.25
            elif wind > 30:  # High winds
                probability += 0.1
        
        if 'snow_cm' in features_dict:
            snow = features_dict['snow_cm']
            if snow > 10:  # Heavy snow
                probability += 0.2
            elif snow > 5:  # Moderate snow
                probability += 0.1
        
        # Component type factor
        if 'component_type' in features_dict:
            if features_dict['component_type'] == 'line':
                # Lines are typically more vulnerable
                probability *= 1.2
        
        # Cap the probability at a reasonable value
        return min(probability, 0.95)
