import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os
from app import db
from models import Trip, BoatType

class FuelPredictor:
    """Machine learning model for fuel consumption prediction"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.is_trained = False
        
        # Try to load pre-trained models
        self.load_models()
    
    def prepare_features(self, data):
        """Prepare features for training or prediction"""
        features = {}
        
        # Numeric features
        features['distance_km'] = data.get('distance_km', 0)
        features['avg_speed'] = data.get('avg_speed', 15)
        features['current_speed'] = data.get('current_speed', 2.5)
        features['fuel_efficiency_factor'] = data.get('fuel_efficiency_factor', 1.0)
        
        # Categorical features
        features['boat_type'] = data.get('boat_type', 'medium')
        features['weather_condition'] = data.get('weather_condition', 'clear')
        
        return features
    
    def train_models(self, training_data):
        """Train multiple regression models"""
        if len(training_data) < 10:
            # Generate synthetic training data based on physics principles
            training_data = self.generate_synthetic_training_data()
        
        df = pd.DataFrame(training_data)
        
        # Prepare features
        feature_columns = ['distance_km', 'avg_speed', 'current_speed', 'fuel_efficiency_factor']
        categorical_columns = ['boat_type', 'weather_condition']
        
        # Encode categorical features
        for col in categorical_columns:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
            df[f'{col}_encoded'] = self.encoders[col].fit_transform(df[col].astype(str))
            feature_columns.append(f'{col}_encoded')
        
        X = df[feature_columns]
        y = df['fuel_consumption']
        
        # Scale features
        self.scalers['features'] = StandardScaler()
        X_scaled = self.scalers['features'].fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train multiple models
        models_to_train = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42)
        }
        
        self.model_performance = {}
        
        for name, model in models_to_train.items():
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            self.models[name] = model
            self.model_performance[name] = {
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'accuracy': max(0, min(100, 100 - (mae / np.mean(y_test)) * 100))
            }
            
            print(f"{name} - MAE: {mae:.2f}, MSE: {mse:.2f}, R²: {r2:.3f}, Accuracy: {self.model_performance[name]['accuracy']:.1f}%")
        
        # Select best model based on accuracy
        best_model_name = max(self.model_performance.keys(), 
                             key=lambda x: self.model_performance[x]['accuracy'])
        self.best_model_name = best_model_name
        
        print(f"Best model: {best_model_name} with {self.model_performance[best_model_name]['accuracy']:.1f}% accuracy")
        
        self.is_trained = True
        self.save_models()
    
    def predict_fuel_consumption(self, route_features):
        """Predict fuel consumption for a given route"""
        if not self.is_trained:
            # Use physics-based estimation if no trained model
            return self.physics_based_estimation(route_features)
        
        features = self.prepare_features(route_features)
        
        # Prepare feature vector
        feature_vector = [
            features['distance_km'],
            features['avg_speed'],
            features['current_speed'],
            features['fuel_efficiency_factor']
        ]
        
        # Encode categorical features
        for col in ['boat_type', 'weather_condition']:
            if col in self.encoders:
                try:
                    encoded_val = self.encoders[col].transform([features[col]])[0]
                except ValueError:
                    # Handle unseen categories
                    encoded_val = 0
            else:
                encoded_val = 0
            feature_vector.append(encoded_val)
        
        # Scale features
        if 'features' in self.scalers:
            feature_vector = self.scalers['features'].transform([feature_vector])
        
        # Make prediction using best model
        if self.best_model_name in self.models:
            prediction = self.models[self.best_model_name].predict(feature_vector)[0]
        else:
            prediction = self.physics_based_estimation(route_features)
        
        return max(1.0, prediction)  # Ensure minimum fuel consumption
    
    def physics_based_estimation(self, route_features):
        """Physics-based fuel consumption estimation"""
        distance = route_features.get('distance_km', 0)
        speed = route_features.get('avg_speed', 15)
        efficiency_factor = route_features.get('fuel_efficiency_factor', 1.0)
        current_speed = route_features.get('current_speed', 2.5)
        
        # Base fuel consumption: ~2.5 liters per km for medium boats
        base_consumption = 2.5
        
        # Adjust for speed (higher speed = more fuel)
        speed_factor = (speed / 15) ** 1.5
        
        # Adjust for current (against current = more fuel)
        current_factor = 1 + (current_speed / 10)
        
        # Weather factor
        weather = route_features.get('weather_condition', 'clear')
        weather_factors = {
            'clear': 1.0,
            'cloudy': 1.1,
            'rainy': 1.2,
            'stormy': 1.4
        }
        weather_factor = weather_factors.get(weather, 1.0)
        
        estimated_fuel = (distance * base_consumption * speed_factor * 
                         current_factor * weather_factor * efficiency_factor)
        
        return max(1.0, estimated_fuel)
    
    def generate_synthetic_training_data(self):
        """Generate synthetic training data based on physics principles"""
        np.random.seed(42)
        training_data = []
        
        boat_types = ['small', 'medium', 'large']
        weather_conditions = ['clear', 'cloudy', 'rainy', 'stormy']
        
        for _ in range(1000):
            distance = np.random.uniform(5, 200)  # 5-200 km
            boat_type = np.random.choice(boat_types)
            weather = np.random.choice(weather_conditions)
            
            # Speed based on boat type
            speed_ranges = {'small': (10, 18), 'medium': (15, 25), 'large': (20, 30)}
            speed = np.random.uniform(*speed_ranges[boat_type])
            
            current_speed = np.random.uniform(1, 5)
            
            # Efficiency factors
            efficiency_factors = {'small': 0.8, 'medium': 1.0, 'large': 1.3}
            efficiency = efficiency_factors[boat_type] * np.random.uniform(0.9, 1.1)
            
            # Calculate fuel consumption using physics-based model
            route_features = {
                'distance_km': distance,
                'avg_speed': speed,
                'current_speed': current_speed,
                'fuel_efficiency_factor': efficiency,
                'boat_type': boat_type,
                'weather_condition': weather
            }
            
            fuel_consumption = self.physics_based_estimation(route_features)
            
            # Add some realistic noise
            fuel_consumption *= np.random.uniform(0.85, 1.15)
            
            training_data.append({
                'distance_km': distance,
                'avg_speed': speed,
                'current_speed': current_speed,
                'fuel_efficiency_factor': efficiency,
                'boat_type': boat_type,
                'weather_condition': weather,
                'fuel_consumption': fuel_consumption
            })
        
        return training_data
    
    def save_models(self):
        """Save trained models to disk"""
        os.makedirs('saved_models', exist_ok=True)
        
        for name, model in self.models.items():
            joblib.dump(model, f'saved_models/{name}_model.pkl')
        
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'saved_models/{name}_scaler.pkl')
        
        for name, encoder in self.encoders.items():
            joblib.dump(encoder, f'saved_models/{name}_encoder.pkl')
        
        # Save metadata
        metadata = {
            'best_model_name': getattr(self, 'best_model_name', 'physics'),
            'model_performance': getattr(self, 'model_performance', {}),
            'is_trained': self.is_trained
        }
        joblib.dump(metadata, 'saved_models/metadata.pkl')
    
    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            # Load metadata
            metadata = joblib.load('saved_models/metadata.pkl')
            self.best_model_name = metadata.get('best_model_name', 'physics')
            self.model_performance = metadata.get('model_performance', {})
            self.is_trained = metadata.get('is_trained', False)
            
            # Load models
            model_files = ['linear_regression_model.pkl', 'random_forest_model.pkl', 'xgboost_model.pkl']
            for file in model_files:
                name = file.replace('_model.pkl', '')
                try:
                    self.models[name] = joblib.load(f'saved_models/{file}')
                except FileNotFoundError:
                    continue
            
            # Load scalers and encoders
            try:
                self.scalers['features'] = joblib.load('saved_models/features_scaler.pkl')
            except FileNotFoundError:
                pass
            
            encoder_files = ['boat_type_encoder.pkl', 'weather_condition_encoder.pkl']
            for file in encoder_files:
                name = file.replace('_encoder.pkl', '')
                try:
                    self.encoders[name] = joblib.load(f'saved_models/{file}')
                except FileNotFoundError:
                    continue
            
            print(f"Loaded models successfully. Best model: {self.best_model_name}")
            
        except FileNotFoundError:
            print("No pre-trained models found. Will train on first use.")
            self.is_trained = False


def train_and_save_models():
    """Train and save ML models using database data"""
    # Get trip data from database
    trips = Trip.query.filter(Trip.actual_fuel_used.isnot(None)).all()
    
    training_data = []
    for trip in trips:
        boat_type = trip.boat_type.name if trip.boat_type else 'medium'
        
        # Calculate approximate distance (simplified)
        distance = ((trip.to_terminal.latitude - trip.from_terminal.latitude) ** 2 +
                   (trip.to_terminal.longitude - trip.from_terminal.longitude) ** 2) ** 0.5 * 111  # Rough km conversion
        
        training_data.append({
            'distance_km': distance,
            'avg_speed': trip.boat_type.avg_speed_kmh if trip.boat_type else 20,
            'current_speed': trip.current_speed or 2.5,
            'fuel_efficiency_factor': trip.boat_type.fuel_efficiency_factor if trip.boat_type else 1.0,
            'boat_type': boat_type,
            'weather_condition': trip.weather_condition or 'clear',
            'fuel_consumption': trip.actual_fuel_used
        })
    
    # Initialize and train predictor
    predictor = FuelPredictor()
    predictor.train_models(training_data)
    
    return predictor
