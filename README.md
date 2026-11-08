# AI-Powered-River-Navigation-System-
AI-powered river navigation and fuel optimization system for Bangladesh’s inland waterways, combining ML fuel prediction with graph-based route planning (Dijkstra and A*).
AI-Powered River Navigation & Fuel Optimization

A Flask-based web application that helps launch boat operators in Bangladesh plan efficient river routes and estimate fuel needs before a trip. It combines machine learning with graph algorithms to support safer, cheaper and faster river transport.

Key Features

Route Optimization: Finds the best path between river terminals using Dijkstra and A* on a NetworkX graph, with edge weights adjusted for distance, river current and route difficulty.
Alternative Routes: Suggests backup routes, such as ones that avoid high-current stretches or take the shortest distance.
Fuel Prediction: Estimates fuel consumption with Linear Regression, Random Forest and XGBoost models, and selects the best performer. It falls back to a physics-based estimate when training data is limited.
Trip Planning: Checks whether the available fuel is enough for the journey and predicts travel time for different boat types.
Interactive Maps: Visualizes the optimal and alternative routes with Folium.
Analytics Dashboard: Tracks prediction accuracy, popular routes and monthly trip trends.

Tech Stack
Python, Flask, SQLAlchemy, SQLite/PostgreSQL, Scikit-learn, XGBoost, NetworkX, Pandas, NumPy, Folium, Bootstrap 5, Chart.js

pip install -r requirements.txt
python main.py
