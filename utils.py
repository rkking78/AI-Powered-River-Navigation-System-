import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )

def calculate_accuracy(predicted, actual):
    """Calculate prediction accuracy percentage"""
    if not predicted or not actual:
        return 0
    
    error_percentage = abs(predicted - actual) / actual * 100
    accuracy = max(0, 100 - error_percentage)
    return round(accuracy, 2)

def format_duration(hours):
    """Format duration in hours to human readable format"""
    if not hours:
        return "N/A"
    
    total_minutes = int(hours * 60)
    hours_int = total_minutes // 60
    minutes = total_minutes % 60
    
    if hours_int > 0:
        return f"{hours_int}h {minutes}m"
    else:
        return f"{minutes}m"

def format_distance(km):
    """Format distance with appropriate units"""
    if not km:
        return "N/A"
    
    if km < 1:
        return f"{int(km * 1000)}m"
    else:
        return f"{km:.1f}km"

def format_fuel(liters):
    """Format fuel consumption"""
    if not liters:
        return "N/A"
    
    return f"{liters:.1f}L"

def validate_coordinates(lat, lon):
    """Validate latitude and longitude coordinates"""
    try:
        lat = float(lat)
        lon = float(lon)
        
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True, lat, lon
        else:
            return False, None, None
    except (ValueError, TypeError):
        return False, None, None

def calculate_route_efficiency(predicted_fuel, actual_fuel, predicted_time, actual_time):
    """Calculate overall route efficiency score"""
    fuel_efficiency = calculate_accuracy(predicted_fuel, actual_fuel)
    time_efficiency = calculate_accuracy(predicted_time, actual_time)
    
    # Weighted average (fuel is more important)
    overall_efficiency = (fuel_efficiency * 0.7 + time_efficiency * 0.3)
    return round(overall_efficiency, 1)

def get_weather_impact_factor(weather_condition):
    """Get weather impact factor for calculations"""
    weather_factors = {
        'clear': 1.0,
        'cloudy': 1.1,
        'rainy': 1.25,
        'stormy': 1.5,
        'foggy': 1.3
    }
    return weather_factors.get(weather_condition.lower(), 1.0)

def get_seasonal_factor(date):
    """Get seasonal factor for fuel consumption"""
    if not isinstance(date, datetime):
        return 1.0
    
    day_of_year = date.timetuple().tm_yday
    
    # Winter (Dec-Feb): slightly higher fuel consumption
    if day_of_year <= 60 or day_of_year >= 335:
        return 1.05
    # Monsoon (Jun-Sep): higher fuel consumption due to rough waters
    elif 150 <= day_of_year <= 270:
        return 1.15
    # Spring/Autumn: optimal conditions
    else:
        return 1.0

def export_route_report(trip_data, filename=None):
    """Export route analysis to a formatted report"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"route_report_{timestamp}.json"
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'trip_summary': {
            'from_terminal': trip_data.get('from_terminal'),
            'to_terminal': trip_data.get('to_terminal'),
            'total_distance': trip_data.get('total_distance'),
            'predicted_fuel': trip_data.get('predicted_fuel'),
            'predicted_time': trip_data.get('predicted_time'),
            'weather_condition': trip_data.get('weather_condition')
        },
        'route_segments': trip_data.get('route_segments', []),
        'alternative_routes': trip_data.get('alternative_routes', []),
        'efficiency_metrics': {
            'fuel_efficiency_rating': trip_data.get('fuel_efficiency_rating'),
            'time_efficiency_rating': trip_data.get('time_efficiency_rating'),
            'overall_score': trip_data.get('overall_score')
        }
    }
    
    os.makedirs('reports', exist_ok=True)
    
    with open(f'reports/{filename}', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return filename

def parse_route_coordinates(route_json_string):
    """Parse route coordinates from JSON string"""
    try:
        if isinstance(route_json_string, str):
            return json.loads(route_json_string)
        return route_json_string
    except (json.JSONDecodeError, TypeError):
        return []

def calculate_carbon_footprint(fuel_consumption):
    """Calculate estimated carbon footprint from fuel consumption"""
    # Approximate CO2 emission: 2.68 kg CO2 per liter of diesel
    if not fuel_consumption:
        return 0
    
    co2_per_liter = 2.68  # kg CO2
    carbon_footprint = fuel_consumption * co2_per_liter
    return round(carbon_footprint, 2)

def get_river_condition_status(current_speed, weather_condition):
    """Determine river condition status"""
    base_score = 100
    
    # Current speed impact
    if current_speed > 4.0:
        base_score -= 30
    elif current_speed > 3.0:
        base_score -= 15
    elif current_speed > 2.5:
        base_score -= 5
    
    # Weather impact
    weather_impacts = {
        'clear': 0,
        'cloudy': -5,
        'rainy': -20,
        'stormy': -40,
        'foggy': -25
    }
    
    base_score += weather_impacts.get(weather_condition.lower(), 0)
    
    # Determine status
    if base_score >= 80:
        return 'Excellent', 'green'
    elif base_score >= 60:
        return 'Good', 'lightgreen'
    elif base_score >= 40:
        return 'Fair', 'orange'
    else:
        return 'Poor', 'red'

def generate_route_suggestions(trip_data):
    """Generate route optimization suggestions"""
    suggestions = []
    
    # Fuel efficiency suggestions
    if trip_data.get('predicted_fuel', 0) > trip_data.get('boat_fuel_capacity', 1000) * 0.8:
        suggestions.append({
            'type': 'warning',
            'category': 'Fuel Management',
            'message': 'High fuel consumption predicted. Consider carrying extra fuel or choosing a more fuel-efficient boat.',
            'priority': 'high'
        })
    
    # Weather-based suggestions
    weather = trip_data.get('weather_condition', '').lower()
    if weather in ['stormy', 'rainy']:
        suggestions.append({
            'type': 'caution',
            'category': 'Weather Advisory',
            'message': f'{weather.title()} conditions expected. Allow extra time and ensure safety equipment is ready.',
            'priority': 'high'
        })
    
    # Current speed suggestions
    current_speed = trip_data.get('avg_current_speed', 0)
    if current_speed > 3.5:
        suggestions.append({
            'type': 'info',
            'category': 'Navigation',
            'message': 'High current speed detected. Consider alternative routes or adjust departure time.',
            'priority': 'medium'
        })
    
    # Time optimization
    predicted_time = trip_data.get('predicted_time', 0)
    if predicted_time > 8:  # More than 8 hours
        suggestions.append({
            'type': 'info',
            'category': 'Journey Planning',
            'message': 'Long journey detected. Plan for rest stops and ensure adequate provisions.',
            'priority': 'medium'
        })
    
    return suggestions

class DataValidator:
    """Data validation utility class"""
    
    @staticmethod
    def validate_terminal_data(data):
        """Validate terminal data"""
        required_fields = ['name', 'code', 'latitude', 'longitude']
        errors = []
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate coordinates
        if data.get('latitude') and data.get('longitude'):
            valid, _, _ = validate_coordinates(data['latitude'], data['longitude'])
            if not valid:
                errors.append("Invalid coordinates")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_trip_data(data):
        """Validate trip planning data"""
        required_fields = ['from_terminal', 'to_terminal', 'boat_type', 'fuel_amount', 'travel_date']
        errors = []
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate fuel amount
        if data.get('fuel_amount'):
            try:
                fuel = float(data['fuel_amount'])
                if fuel <= 0:
                    errors.append("Fuel amount must be positive")
            except (ValueError, TypeError):
                errors.append("Invalid fuel amount")
        
        # Validate date
        if data.get('travel_date'):
            try:
                travel_date = datetime.strptime(data['travel_date'], '%Y-%m-%d')
                if travel_date < datetime.now() - timedelta(days=1):
                    errors.append("Travel date cannot be in the past")
            except ValueError:
                errors.append("Invalid date format")
        
        return len(errors) == 0, errors

# Global utility functions
def safe_divide(numerator, denominator):
    """Safe division that handles zero denominators"""
    try:
        return numerator / denominator if denominator != 0 else 0
    except (TypeError, ValueError):
        return 0

def clamp(value, min_value, max_value):
    """Clamp value between min and max"""
    return max(min_value, min(value, max_value))
