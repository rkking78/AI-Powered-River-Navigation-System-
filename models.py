from datetime import datetime
from app import db

class Terminal(db.Model):
    """River terminals/stations model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    division = db.Column(db.String(50))
    district = db.Column(db.String(50))
    river_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Terminal {self.name}>'

class Route(db.Model):
    """River routes between terminals"""
    id = db.Column(db.Integer, primary_key=True)
    from_terminal_id = db.Column(db.Integer, db.ForeignKey('terminal.id'), nullable=False)
    to_terminal_id = db.Column(db.Integer, db.ForeignKey('terminal.id'), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    avg_current_speed = db.Column(db.Float, default=2.5)  # km/h
    difficulty_level = db.Column(db.String(20), default='medium')
    
    from_terminal = db.relationship('Terminal', foreign_keys=[from_terminal_id], backref='outgoing_routes')
    to_terminal = db.relationship('Terminal', foreign_keys=[to_terminal_id], backref='incoming_routes')

class BoatType(db.Model):
    """Different types of launch boats"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity_passengers = db.Column(db.Integer)
    fuel_tank_capacity = db.Column(db.Float)  # liters
    avg_speed_kmh = db.Column(db.Float)
    fuel_efficiency_factor = db.Column(db.Float, default=1.0)

class Trip(db.Model):
    """Historical trip records"""
    id = db.Column(db.Integer, primary_key=True)
    from_terminal_id = db.Column(db.Integer, db.ForeignKey('terminal.id'), nullable=False)
    to_terminal_id = db.Column(db.Integer, db.ForeignKey('terminal.id'), nullable=False)
    boat_type_id = db.Column(db.Integer, db.ForeignKey('boat_type.id'), nullable=False)
    
    fuel_amount = db.Column(db.Float)  # liters
    predicted_fuel = db.Column(db.Float)
    actual_fuel_used = db.Column(db.Float)
    
    travel_date = db.Column(db.DateTime, nullable=False)
    predicted_time_hours = db.Column(db.Float)
    actual_time_hours = db.Column(db.Float)
    
    weather_condition = db.Column(db.String(50))
    current_speed = db.Column(db.Float)
    
    route_taken = db.Column(db.Text)  # JSON string of route coordinates
    alternative_routes = db.Column(db.Text)  # JSON string of alternative routes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    from_terminal = db.relationship('Terminal', foreign_keys=[from_terminal_id])
    to_terminal = db.relationship('Terminal', foreign_keys=[to_terminal_id])
    boat_type = db.relationship('BoatType', backref='trips')

class WeatherData(db.Model):
    """Weather conditions for route planning"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100))  # Division/District
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    weather_condition = db.Column(db.String(50))
    visibility_km = db.Column(db.Float)
