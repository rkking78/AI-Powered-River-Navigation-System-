from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import json
import pandas as pd
import numpy as np
from app import app, db
from models import Terminal, Route, BoatType, Trip, WeatherData
from ml_models import FuelPredictor, train_and_save_models
from graph_algorithms import RouteOptimizer
from data_processor import load_sample_data
import folium
from folium import plugins
import os

# Initialize ML models and route optimizer - will be created on first use
fuel_predictor = None
route_optimizer = None

def get_fuel_predictor():
    global fuel_predictor
    if fuel_predictor is None:
        fuel_predictor = FuelPredictor()
    return fuel_predictor

def get_route_optimizer():
    global route_optimizer
    if route_optimizer is None:
        route_optimizer = RouteOptimizer()
    return route_optimizer

@app.route('/')
def index():
    """Main dashboard page"""
    # Get recent trips for dashboard stats
    recent_trips = Trip.query.order_by(Trip.created_at.desc()).limit(10).all()
    total_trips = Trip.query.count()
    terminals = Terminal.query.all()
    
    return render_template('index.html', 
                         recent_trips=recent_trips,
                         total_trips=total_trips,
                         total_terminals=len(terminals))

@app.route('/route-planner')
def route_planner():
    """Route planning interface"""
    terminals = Terminal.query.all()
    boat_types = BoatType.query.all()
    
    return render_template('route_planner.html', 
                         terminals=terminals, 
                         boat_types=boat_types)

@app.route('/plan-route', methods=['POST'])
def plan_route():
    """Process route planning request"""
    try:
        # Get form data
        from_terminal_id = int(request.form.get('from_terminal'))
        to_terminal_id = int(request.form.get('to_terminal'))
        boat_type_id = int(request.form.get('boat_type'))
        fuel_amount = float(request.form.get('fuel_amount'))
        travel_date_str = request.form.get('travel_date')
        travel_time_str = request.form.get('travel_time')
        
        # Parse date and time
        travel_datetime = datetime.strptime(f"{travel_date_str} {travel_time_str}", "%Y-%m-%d %H:%M")
        
        # Get terminal and boat information with session management
        from_terminal = db.session.get(Terminal, from_terminal_id)
        to_terminal = db.session.get(Terminal, to_terminal_id)
        boat_type = db.session.get(BoatType, boat_type_id)
        
        if not from_terminal or not to_terminal or not boat_type:
            flash('Invalid terminal or boat type selected', 'error')
            return redirect(url_for('route_planner'))
        
        # Find optimal route using graph algorithms
        optimal_route = get_route_optimizer().find_optimal_route(from_terminal_id, to_terminal_id)
        alternative_routes = get_route_optimizer().find_alternative_routes(from_terminal_id, to_terminal_id, top_k=3)
        
        # Predict fuel consumption
        route_features = {
            'distance_km': optimal_route['total_distance'],
            'boat_type': boat_type.name,
            'avg_speed': boat_type.avg_speed_kmh,
            'current_speed': optimal_route['avg_current_speed'],
            'weather_condition': 'clear',  # Default - could be enhanced with weather API
            'fuel_efficiency_factor': boat_type.fuel_efficiency_factor
        }
        
        predicted_fuel = get_fuel_predictor().predict_fuel_consumption(route_features)
        predicted_time = optimal_route['total_distance'] / boat_type.avg_speed_kmh
        
        # Check if fuel amount is sufficient
        fuel_sufficient = fuel_amount >= predicted_fuel
        
        # Create trip record
        trip = Trip(
            from_terminal_id=from_terminal_id,
            to_terminal_id=to_terminal_id,
            boat_type_id=boat_type_id,
            fuel_amount=fuel_amount,
            predicted_fuel=predicted_fuel,
            travel_date=travel_datetime,
            predicted_time_hours=predicted_time,
            weather_condition='clear',
            current_speed=optimal_route['avg_current_speed'],
            route_taken=json.dumps(optimal_route),
            alternative_routes=json.dumps(alternative_routes)
        )
        
        db.session.add(trip)
        db.session.commit()
        
        # Generate map visualization
        map_html = generate_route_map(from_terminal, to_terminal, optimal_route, alternative_routes)
        
        return render_template('results.html',
                             trip=trip,
                             from_terminal=from_terminal,
                             to_terminal=to_terminal,
                             boat_type=boat_type,
                             optimal_route=optimal_route,
                             alternative_routes=alternative_routes,
                             predicted_fuel=predicted_fuel,
                             predicted_time=predicted_time,
                             fuel_sufficient=fuel_sufficient,
                             map_html=map_html)
        
    except Exception as e:
        app.logger.error(f"Error in route planning: {str(e)}")
        flash(f'Error planning route: {str(e)}', 'error')
        return redirect(url_for('route_planner'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    # Get trip statistics
    total_trips = Trip.query.count()
    
    # Fuel prediction accuracy
    trips_with_actual = Trip.query.filter(Trip.actual_fuel_used.isnot(None)).all()
    accuracy_data = []
    
    for trip in trips_with_actual:
        accuracy = 100 - abs(trip.predicted_fuel - trip.actual_fuel_used) / trip.actual_fuel_used * 100
        accuracy_data.append(accuracy)
    
    avg_accuracy = np.mean(accuracy_data) if accuracy_data else 0
    
    # Popular routes
    popular_routes = db.session.query(
        Trip.from_terminal_id, 
        Trip.to_terminal_id, 
        db.func.count(Trip.id).label('trip_count')
    ).group_by(Trip.from_terminal_id, Trip.to_terminal_id).order_by(
        db.func.count(Trip.id).desc()
    ).limit(5).all()
    
    # Monthly trip trends
    monthly_trips = db.session.query(
        db.func.strftime('%Y-%m', Trip.created_at).label('month'),
        db.func.count(Trip.id).label('trip_count')
    ).group_by(db.func.strftime('%Y-%m', Trip.created_at)).order_by('month').all()
    
    return render_template('analytics.html',
                         total_trips=total_trips,
                         avg_accuracy=avg_accuracy,
                         popular_routes=popular_routes,
                         monthly_trips=monthly_trips,
                         accuracy_data=accuracy_data,
                         datetime=datetime)

@app.route('/initialize-data')
def initialize_data():
    """Initialize the database with sample data"""
    try:
        load_sample_data()
        # Train and save ML models
        train_and_save_models()
        flash('Database initialized successfully with sample data', 'success')
    except Exception as e:
        app.logger.error(f"Error initializing data: {str(e)}")
        flash(f'Error initializing data: {str(e)}', 'error')
    
    return redirect(url_for('index'))

def generate_route_map(from_terminal, to_terminal, optimal_route, alternative_routes):
    """Generate an interactive map with route visualization"""
    # Create a map centered on Bangladesh
    center_lat = (from_terminal.latitude + to_terminal.latitude) / 2
    center_lon = (from_terminal.longitude + to_terminal.longitude) / 2
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
    
    # Add source and destination markers
    folium.Marker(
        [from_terminal.latitude, from_terminal.longitude],
        popup=f"From: {from_terminal.name}",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    folium.Marker(
        [to_terminal.latitude, to_terminal.longitude],
        popup=f"To: {to_terminal.name}",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)
    
    # Add optimal route line
    if 'route_coordinates' in optimal_route:
        folium.PolyLine(
            optimal_route['route_coordinates'],
            weight=5,
            color='blue',
            popup='Optimal Route'
        ).add_to(m)
    
    # Add alternative routes
    colors = ['purple', 'orange', 'darkgreen']
    for i, alt_route in enumerate(alternative_routes[:3]):
        if 'route_coordinates' in alt_route:
            folium.PolyLine(
                alt_route['route_coordinates'],
                weight=3,
                color=colors[i % len(colors)],
                popup=f'Alternative Route {i+1}'
            ).add_to(m)
    
    # Convert map to HTML
    return m._repr_html_()

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
