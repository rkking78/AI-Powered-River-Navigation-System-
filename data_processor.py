import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app import db
from models import Terminal, Route, BoatType, Trip, WeatherData
import os
import random

def load_sample_data():
    """Load sample data into the database"""
    # Clear existing data
    db.session.query(Trip).delete()
    db.session.query(WeatherData).delete()
    db.session.query(Route).delete()
    db.session.query(BoatType).delete()
    db.session.query(Terminal).delete()
    
    # Load terminals (major river ports in Bangladesh)
    terminals_data = [
        # Dhaka Division
        {'name': 'Sadarghat Terminal', 'code': 'SGT', 'lat': 23.7104, 'lon': 90.4074, 'division': 'Dhaka', 'district': 'Dhaka', 'river': 'Buriganga'},
        {'name': 'Narayanganj Terminal', 'code': 'NGT', 'lat': 23.6238, 'lon': 90.4969, 'division': 'Dhaka', 'district': 'Narayanganj', 'river': 'Shitalakshya'},
        {'name': 'Munshiganj Terminal', 'code': 'MGT', 'lat': 23.5422, 'lon': 90.5305, 'division': 'Dhaka', 'district': 'Munshiganj', 'river': 'Padma'},
        
        # Chattogram Division
        {'name': 'Chattogram Port', 'code': 'CTP', 'lat': 22.3569, 'lon': 91.7832, 'division': 'Chattogram', 'district': 'Chattogram', 'river': 'Karnaphuli'},
        {'name': 'Chandpur Terminal', 'code': 'CPT', 'lat': 23.2513, 'lon': 90.8518, 'division': 'Chattogram', 'district': 'Chandpur', 'river': 'Meghna'},
        
        # Khulna Division
        {'name': 'Khulna Terminal', 'code': 'KHT', 'lat': 22.8456, 'lon': 89.5403, 'division': 'Khulna', 'district': 'Khulna', 'river': 'Rupsha'},
        {'name': 'Mongla Port', 'code': 'MLP', 'lat': 22.4869, 'lon': 89.5947, 'division': 'Khulna', 'district': 'Bagerhat', 'river': 'Passur'},
        {'name': 'Barisal Terminal', 'code': 'BST', 'lat': 22.7010, 'lon': 90.3535, 'division': 'Barisal', 'district': 'Barisal', 'river': 'Kirtankhola'},
        
        # Sylhet Division
        {'name': 'Sylhet Terminal', 'code': 'SYT', 'lat': 24.8949, 'lon': 91.8687, 'division': 'Sylhet', 'district': 'Sylhet', 'river': 'Surma'},
        
        # Rangpur Division
        {'name': 'Rangpur Terminal', 'code': 'RPT', 'lat': 25.7439, 'lon': 89.2752, 'division': 'Rangpur', 'district': 'Rangpur', 'river': 'Ghaghat'},
        
        # Rajshahi Division
        {'name': 'Rajshahi Terminal', 'code': 'RJT', 'lat': 24.3745, 'lon': 88.6042, 'division': 'Rajshahi', 'district': 'Rajshahi', 'river': 'Padma'},
        {'name': 'Pabna Terminal', 'code': 'PBT', 'lat': 24.0064, 'lon': 89.2372, 'division': 'Rajshahi', 'district': 'Pabna', 'river': 'Padma'},
        
        # Mymensingh Division
        {'name': 'Mymensingh Terminal', 'code': 'MYT', 'lat': 24.7471, 'lon': 90.4203, 'division': 'Mymensingh', 'district': 'Mymensingh', 'river': 'Brahmaputra'},
    ]
    
    for terminal_data in terminals_data:
        terminal = Terminal(
            name=terminal_data['name'],
            code=terminal_data['code'],
            latitude=terminal_data['lat'],
            longitude=terminal_data['lon'],
            division=terminal_data['division'],
            district=terminal_data['district'],
            river_name=terminal_data['river']
        )
        db.session.add(terminal)
    
    db.session.commit()
    
    # Load boat types
    boat_types_data = [
        {'name': 'Small Launch', 'capacity': 50, 'fuel_tank': 200, 'avg_speed': 15, 'efficiency': 0.8},
        {'name': 'Medium Launch', 'capacity': 150, 'fuel_tank': 500, 'avg_speed': 20, 'efficiency': 1.0},
        {'name': 'Large Launch', 'capacity': 300, 'fuel_tank': 800, 'avg_speed': 25, 'efficiency': 1.3},
        {'name': 'Speed Boat', 'capacity': 20, 'fuel_tank': 100, 'avg_speed': 35, 'efficiency': 0.6},
        {'name': 'Cargo Vessel', 'capacity': 500, 'fuel_tank': 1500, 'avg_speed': 18, 'efficiency': 1.8},
    ]
    
    for boat_data in boat_types_data:
        boat_type = BoatType(
            name=boat_data['name'],
            capacity_passengers=boat_data['capacity'],
            fuel_tank_capacity=boat_data['fuel_tank'],
            avg_speed_kmh=boat_data['avg_speed'],
            fuel_efficiency_factor=boat_data['efficiency']
        )
        db.session.add(boat_type)
    
    db.session.commit()
    
    # Create routes between terminals
    terminals = Terminal.query.all()
    terminal_dict = {t.id: t for t in terminals}
    
    # Define major route connections (simplified network)
    route_connections = [
        # Dhaka-centered routes
        (1, 2, 15.2, 2.3, 'medium'),  # Sadarghat to Narayanganj
        (1, 3, 25.8, 2.8, 'medium'),  # Sadarghat to Munshiganj
        (1, 5, 45.6, 3.2, 'medium'),  # Sadarghat to Chandpur
        (1, 8, 120.5, 2.5, 'medium'), # Sadarghat to Barisal
        
        # Cross-regional routes
        (2, 3, 12.4, 2.1, 'easy'),    # Narayanganj to Munshiganj
        (3, 5, 35.2, 3.0, 'medium'),  # Munshiganj to Chandpur
        (5, 4, 85.3, 3.5, 'hard'),    # Chandpur to Chattogram
        (5, 8, 95.7, 2.8, 'medium'),  # Chandpur to Barisal
        
        # Southern routes
        (6, 7, 45.8, 2.2, 'easy'),    # Khulna to Mongla
        (6, 8, 55.3, 2.6, 'medium'),  # Khulna to Barisal
        (8, 1, 120.5, 2.5, 'medium'), # Barisal to Sadarghat (reverse)
        
        # Northern routes
        (9, 13, 185.4, 1.8, 'easy'),  # Sylhet to Mymensingh
        (10, 11, 95.6, 2.0, 'medium'), # Rangpur to Rajshahi
        (11, 12, 42.7, 2.3, 'easy'),  # Rajshahi to Pabna
        (12, 13, 78.9, 2.1, 'medium'), # Pabna to Mymensingh
        (13, 1, 125.8, 2.4, 'medium'), # Mymensingh to Sadarghat
    ]
    
    for from_id, to_id, distance, current_speed, difficulty in route_connections:
        route = Route(
            from_terminal_id=from_id,
            to_terminal_id=to_id,
            distance_km=distance,
            avg_current_speed=current_speed,
            difficulty_level=difficulty
        )
        db.session.add(route)
    
    db.session.commit()
    
    # Generate historical trip data
    generate_historical_trips()
    
    # Generate weather data
    generate_weather_data()
    
    print("Sample data loaded successfully!")

def generate_historical_trips():
    """Generate historical trip data for training ML models"""
    terminals = Terminal.query.all()
    boat_types = BoatType.query.all()
    routes = Route.query.all()
    
    if not terminals or not boat_types or not routes:
        print("Missing base data for trip generation")
        return
    
    # Generate trips for the last 12 months
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    weather_conditions = ['clear', 'cloudy', 'rainy', 'stormy']
    weather_weights = [0.5, 0.3, 0.15, 0.05]  # More clear days
    
    # Generate 500-1000 historical trips
    for _ in range(random.randint(500, 1000)):
        # Random route selection
        route = random.choice(routes)
        boat_type = random.choice(boat_types)
        
        # Random travel date
        random_days = random.randint(0, (end_date - start_date).days)
        travel_date = start_date + timedelta(days=random_days)
        
        # Weather condition
        weather = np.random.choice(weather_conditions, p=weather_weights)
        
        # Calculate predicted values based on physics model
        distance = route.distance_km
        speed = boat_type.avg_speed_kmh
        current_speed = route.avg_current_speed + random.uniform(-0.5, 0.5)
        
        # Base fuel calculation
        base_fuel_per_km = 2.5 * boat_type.fuel_efficiency_factor
        speed_factor = (speed / 20) ** 1.3
        current_factor = 1 + (current_speed / 10)
        
        weather_factors = {'clear': 1.0, 'cloudy': 1.1, 'rainy': 1.25, 'stormy': 1.5}
        weather_factor = weather_factors[weather]
        
        predicted_fuel = distance * base_fuel_per_km * speed_factor * current_factor * weather_factor
        predicted_time = distance / speed * current_factor * weather_factor
        
        # Add realistic variation for actual values
        actual_fuel = predicted_fuel * random.uniform(0.85, 1.15)
        actual_time = predicted_time * random.uniform(0.9, 1.1)
        
        # Random fuel amount (should be >= actual fuel for successful trips)
        fuel_amount = actual_fuel * random.uniform(1.1, 1.8)
        
        trip = Trip(
            from_terminal_id=route.from_terminal_id,
            to_terminal_id=route.to_terminal_id,
            boat_type_id=boat_type.id,
            fuel_amount=fuel_amount,
            predicted_fuel=predicted_fuel,
            actual_fuel_used=actual_fuel,
            travel_date=travel_date,
            predicted_time_hours=predicted_time,
            actual_time_hours=actual_time,
            weather_condition=weather,
            current_speed=current_speed,
            route_taken=f'[{route.from_terminal_id}, {route.to_terminal_id}]',
            alternative_routes='[]'
        )
        
        db.session.add(trip)
    
    db.session.commit()
    print(f"Generated {Trip.query.count()} historical trips")

def generate_weather_data():
    """Generate historical weather data"""
    divisions = ['Dhaka', 'Chattogram', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet', 'Barisal', 'Mymensingh']
    
    start_date = datetime.now().date() - timedelta(days=365)
    end_date = datetime.now().date()
    
    current_date = start_date
    while current_date <= end_date:
        for division in divisions:
            # Seasonal temperature variations
            day_of_year = current_date.timetuple().tm_yday
            base_temp = 20 + 10 * np.sin((day_of_year - 80) * 2 * np.pi / 365)  # Seasonal variation
            temperature = base_temp + random.uniform(-5, 8)
            
            # Humidity (higher in monsoon season)
            if 150 <= day_of_year <= 270:  # Monsoon season
                humidity = random.uniform(70, 95)
                rain_chance = 0.6
            else:
                humidity = random.uniform(40, 80)
                rain_chance = 0.2
            
            # Weather conditions
            if random.random() < rain_chance:
                if random.random() < 0.1:
                    weather_condition = 'stormy'
                    wind_speed = random.uniform(25, 50)
                    visibility = random.uniform(2, 8)
                else:
                    weather_condition = 'rainy'
                    wind_speed = random.uniform(10, 30)
                    visibility = random.uniform(5, 15)
            elif random.random() < 0.3:
                weather_condition = 'cloudy'
                wind_speed = random.uniform(5, 20)
                visibility = random.uniform(8, 20)
            else:
                weather_condition = 'clear'
                wind_speed = random.uniform(2, 15)
                visibility = random.uniform(15, 30)
            
            weather_data = WeatherData(
                date=current_date,
                location=division,
                temperature=round(temperature, 1),
                humidity=round(humidity, 1),
                wind_speed=round(wind_speed, 1),
                weather_condition=weather_condition,
                visibility_km=round(visibility, 1)
            )
            
            db.session.add(weather_data)
        
        current_date += timedelta(days=1)
    
    db.session.commit()
    print(f"Generated {WeatherData.query.count()} weather records")

def load_csv_data(file_path):
    """Load data from CSV file if available"""
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None

def preprocess_data(df):
    """Preprocess data for ML models"""
    if df is None or df.empty:
        return None
    
    # Handle missing values
    df = df.fillna(df.mean() if df.select_dtypes(include=[np.number]).columns.any() else df.mode().iloc[0])
    
    # Normalize numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        df[col] = (df[col] - df[col].mean()) / df[col].std()
    
    return df

def export_data_to_csv():
    """Export database data to CSV files for external analysis"""
    os.makedirs('exported_data', exist_ok=True)
    
    # Export trips
    trips = Trip.query.all()
    trip_data = []
    for trip in trips:
        trip_data.append({
            'trip_id': trip.id,
            'from_terminal': trip.from_terminal.name,
            'to_terminal': trip.to_terminal.name,
            'boat_type': trip.boat_type.name,
            'travel_date': trip.travel_date,
            'predicted_fuel': trip.predicted_fuel,
            'actual_fuel': trip.actual_fuel_used,
            'fuel_amount': trip.fuel_amount,
            'predicted_time': trip.predicted_time_hours,
            'actual_time': trip.actual_time_hours,
            'weather_condition': trip.weather_condition,
            'current_speed': trip.current_speed
        })
    
    pd.DataFrame(trip_data).to_csv('exported_data/trips.csv', index=False)
    
    # Export terminals
    terminals = Terminal.query.all()
    terminal_data = []
    for terminal in terminals:
        terminal_data.append({
            'id': terminal.id,
            'name': terminal.name,
            'code': terminal.code,
            'latitude': terminal.latitude,
            'longitude': terminal.longitude,
            'division': terminal.division,
            'district': terminal.district,
            'river': terminal.river_name
        })
    
    pd.DataFrame(terminal_data).to_csv('exported_data/terminals.csv', index=False)
    
    print("Data exported to CSV files successfully!")
