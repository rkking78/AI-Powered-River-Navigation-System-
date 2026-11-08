# Overview

The AI-Powered River Navigation & Fuel Optimization system is a Flask-based web application designed for optimizing launch boat routes in Bangladesh's river network. The system combines machine learning algorithms with graph-based route optimization to predict fuel consumption, calculate optimal paths, and provide intelligent navigation recommendations for river transport operators.

The application integrates multiple AI techniques including regression models for fuel prediction, shortest path algorithms (Dijkstra and A*) for route optimization, and data processing capabilities for historical trip analysis. It serves Bangladesh's extensive river transport network by helping operators reduce fuel costs, optimize travel times, and improve overall operational efficiency.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The system uses a traditional server-side rendered architecture with Flask templates and Bootstrap 5 for responsive design. The frontend consists of HTML templates with Jinja2 templating, enhanced with JavaScript for interactive features like form validation, chart visualizations, and map integrations. CSS styling follows a river-themed design system with custom variables for consistent branding.

## Backend Architecture
Built on Flask with SQLAlchemy ORM for database management. The architecture follows a modular design with separated concerns:
- **App Configuration**: Centralized in `app.py` with environment-based settings
- **Models**: SQLAlchemy models for terminals, routes, boat types, trips, and weather data
- **Routes**: Flask route handlers managing HTTP requests and responses
- **Business Logic**: Separated into specialized modules for ML predictions, graph algorithms, and data processing

## Data Storage Solutions
Uses SQLite as the primary database with SQLAlchemy ORM for data management. The database schema includes:
- **Terminals**: River stations with geographical coordinates and metadata
- **Routes**: Connections between terminals with distance and difficulty metrics
- **Trips**: Historical journey records for ML training
- **Boat Types**: Vessel specifications affecting fuel consumption
- **Weather Data**: Environmental factors impacting navigation

The system supports both SQLite for development and can be configured for PostgreSQL in production via environment variables.

## Machine Learning Pipeline
Implements multiple ML approaches:
- **Fuel Prediction**: RandomForest, LinearRegression, and XGBoost models for consumption forecasting
- **Feature Engineering**: Handles numeric (distance, speed, fuel capacity) and categorical (boat type, weather conditions) data
- **Model Persistence**: Uses joblib for saving/loading trained models
- **Synthetic Data Generation**: Physics-based synthetic training data when historical data is insufficient

## Graph-Based Route Optimization
Uses NetworkX for graph operations with custom algorithms:
- **Graph Construction**: Builds directed graphs from terminal and route data
- **Pathfinding**: Implements Dijkstra and A* algorithms for optimal route calculation
- **Weight Adjustment**: Considers current speed, difficulty level, and environmental factors
- **Alternative Routes**: Provides multiple path options with different optimization criteria

# External Dependencies

## Python Libraries
- **Flask**: Web framework for HTTP handling and templating
- **SQLAlchemy**: ORM for database operations and model management
- **Pandas/Numpy**: Data manipulation and numerical computations
- **Scikit-learn**: Machine learning algorithms and preprocessing
- **XGBoost**: Advanced gradient boosting for fuel prediction
- **NetworkX**: Graph algorithms for route optimization
- **Folium**: Interactive map generation for route visualization
- **Joblib**: Model serialization and persistence

## Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **Chart.js**: JavaScript library for data visualizations
- **Custom CSS/JS**: Enhanced styling and interactive features

## Database Integration
- **SQLite**: Default database for development and testing
- **PostgreSQL**: Production database option via DATABASE_URL environment variable
- **Connection Pooling**: Configured for production deployment with pool recycling

## External Data Sources
The system is designed to integrate with:
- **BIWTA**: Bangladesh Inland Water Transport Authority navigation data
- **Bangladesh Meteorological Department**: Weather and river current data
- **Local Operators**: Fuel consumption logs and operational data
- **Satellite/Drone Imagery**: Optional river path obstacle detection

## Deployment Infrastructure
- **Environment Configuration**: Uses environment variables for database URLs and session secrets
- **WSGI Middleware**: ProxyFix for proper handling of reverse proxy headers
- **Debug Logging**: Comprehensive logging setup for development and monitoring
- **Static Assets**: Organized structure for CSS, JavaScript, and image files