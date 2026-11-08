import heapq
import networkx as nx
from collections import defaultdict
import json
import math
from app import db
from models import Terminal, Route

class RouteOptimizer:
    """Graph-based route optimization using Dijkstra and A* algorithms"""
    
    def __init__(self):
        self.graph = None
        self.terminals = {}
        self._graph_built = False
    
    def build_graph(self):
        """Build the river navigation graph from database"""
        if self._graph_built:
            return
            
        self.graph = nx.DiGraph()  # Directed graph for river routes
        
        # Load terminals - store essential data instead of objects to avoid session issues
        terminals = Terminal.query.all()
        for terminal in terminals:
            self.terminals[terminal.id] = {
                'id': terminal.id,
                'name': terminal.name,
                'code': terminal.code,
                'latitude': terminal.latitude,
                'longitude': terminal.longitude,
                'district': terminal.district
            }
            self.graph.add_node(terminal.id, 
                               lat=terminal.latitude, 
                               lon=terminal.longitude,
                               name=terminal.name)
        
        # Load routes
        routes = Route.query.all()
        for route in routes:
            # Add edge with weight as distance (can be modified for fuel cost, time, etc.)
            weight = route.distance_km
            
            # Adjust weight based on current speed (against current increases cost)
            current_factor = 1 + (route.avg_current_speed / 10)  # Higher current = higher cost
            
            # Difficulty adjustment
            difficulty_factors = {'easy': 0.9, 'medium': 1.0, 'hard': 1.3}
            difficulty_factor = difficulty_factors.get(route.difficulty_level, 1.0)
            
            adjusted_weight = weight * current_factor * difficulty_factor
            
            self.graph.add_edge(route.from_terminal_id, route.to_terminal_id, 
                               weight=adjusted_weight,
                               distance=route.distance_km,
                               current_speed=route.avg_current_speed,
                               difficulty=route.difficulty_level)
            
            # Add reverse direction (rivers usually allow both ways)
            self.graph.add_edge(route.to_terminal_id, route.from_terminal_id,
                               weight=adjusted_weight * 1.1,  # Slightly higher cost for reverse
                               distance=route.distance_km,
                               current_speed=route.avg_current_speed,
                               difficulty=route.difficulty_level)
        
        self._graph_built = True
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points on Earth"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def dijkstra_shortest_path(self, start_id, end_id):
        """Find shortest path using Dijkstra's algorithm"""
        self.build_graph()  # Ensure graph is built
        try:
            path = nx.dijkstra_path(self.graph, start_id, end_id, weight='weight')
            path_length = nx.dijkstra_path_length(self.graph, start_id, end_id, weight='weight')
            
            return self.process_path_result(path, path_length)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def a_star_shortest_path(self, start_id, end_id):
        """Find shortest path using A* algorithm with heuristic"""
        self.build_graph()  # Ensure graph is built
        def heuristic(node1, node2):
            if node1 in self.terminals and node2 in self.terminals:
                t1, t2 = self.terminals[node1], self.terminals[node2]
                return self.haversine_distance(t1['latitude'], t1['longitude'], 
                                             t2['latitude'], t2['longitude'])
            return 0
        
        try:
            path = nx.astar_path(self.graph, start_id, end_id, 
                                heuristic=heuristic, weight='weight')
            path_length = nx.astar_path_length(self.graph, start_id, end_id,
                                              heuristic=heuristic, weight='weight')
            
            return self.process_path_result(path, path_length)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def process_path_result(self, path, path_length):
        """Process the path result into a useful format"""
        if not path or len(path) < 2:
            return None
        
        route_info = {
            'path': path,
            'total_distance': 0,
            'total_weight': path_length,
            'segments': [],
            'route_coordinates': [],
            'avg_current_speed': 0
        }
        
        current_speeds = []
        
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            
            if self.graph.has_edge(from_node, to_node):
                edge_data = self.graph[from_node][to_node]
                
                segment = {
                    'from': self.terminals[from_node]['name'],
                    'to': self.terminals[to_node]['name'],
                    'distance': edge_data.get('distance', 0),
                    'current_speed': edge_data.get('current_speed', 2.5),
                    'difficulty': edge_data.get('difficulty', 'medium')
                }
                
                route_info['segments'].append(segment)
                route_info['total_distance'] += segment['distance']
                current_speeds.append(segment['current_speed'])
                
                # Add coordinates for map visualization
                from_terminal = self.terminals[from_node]
                to_terminal = self.terminals[to_node]
                route_info['route_coordinates'].append([from_terminal['latitude'], from_terminal['longitude']])
                
                if i == len(path) - 2:  # Last segment
                    route_info['route_coordinates'].append([to_terminal['latitude'], to_terminal['longitude']])
        
        route_info['avg_current_speed'] = sum(current_speeds) / len(current_speeds) if current_speeds else 2.5
        
        return route_info
    
    def find_optimal_route(self, start_id, end_id, algorithm='a_star'):
        """Find the optimal route between two terminals"""
        if algorithm == 'dijkstra':
            return self.dijkstra_shortest_path(start_id, end_id)
        else:
            # Default to A* for better performance
            result = self.a_star_shortest_path(start_id, end_id)
            if result is None:
                # Fallback to Dijkstra if A* fails
                result = self.dijkstra_shortest_path(start_id, end_id)
            return result
    
    def find_alternative_routes(self, start_id, end_id, top_k=3):
        """Find alternative routes using different approaches"""
        self.build_graph()  # Ensure graph is built
        alternative_routes = []
        
        try:
            # Method 1: K-shortest paths using different weight adjustments
            for weight_factor in [1.2, 1.5, 0.8]:
                temp_graph = self.graph.copy()
                
                # Modify edge weights
                for u, v, data in temp_graph.edges(data=True):
                    temp_graph[u][v]['weight'] = data['weight'] * weight_factor
                
                try:
                    path = nx.dijkstra_path(temp_graph, start_id, end_id, weight='weight')
                    path_length = nx.dijkstra_path_length(temp_graph, start_id, end_id, weight='weight')
                    
                    route = self.process_path_result(path, path_length / weight_factor)  # Normalize back
                    if route and route not in alternative_routes:
                        alternative_routes.append(route)
                except nx.NetworkXNoPath:
                    continue
            
            # Method 2: Find paths avoiding high-current routes
            if len(alternative_routes) < top_k:
                temp_graph = self.graph.copy()
                
                # Remove edges with high current speeds
                edges_to_remove = []
                for u, v, data in temp_graph.edges(data=True):
                    if data.get('current_speed', 0) > 4.0:  # High current threshold
                        edges_to_remove.append((u, v))
                
                temp_graph.remove_edges_from(edges_to_remove)
                
                try:
                    path = nx.dijkstra_path(temp_graph, start_id, end_id, weight='weight')
                    path_length = nx.dijkstra_path_length(temp_graph, start_id, end_id, weight='weight')
                    
                    route = self.process_path_result(path, path_length)
                    if route and route not in alternative_routes:
                        alternative_routes.append(route)
                except nx.NetworkXNoPath:
                    pass
            
            # Method 3: Shortest distance route (ignoring other factors)
            if len(alternative_routes) < top_k:
                try:
                    path = nx.dijkstra_path(self.graph, start_id, end_id, weight='distance')
                    path_length = nx.dijkstra_path_length(self.graph, start_id, end_id, weight='distance')
                    
                    route = self.process_path_result(path, path_length)
                    if route and route not in alternative_routes:
                        alternative_routes.append(route)
                except nx.NetworkXNoPath:
                    pass
                    
        except Exception as e:
            print(f"Error finding alternative routes: {e}")
        
        return alternative_routes[:top_k]
    
    def get_route_statistics(self):
        """Get statistics about the route network"""
        self.build_graph()  # Ensure graph is built
        if not self.graph:
            return {}
        
        return {
            'total_terminals': self.graph.number_of_nodes(),
            'total_routes': self.graph.number_of_edges(),
            'average_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'is_connected': nx.is_connected(self.graph.to_undirected()),
            'diameter': nx.diameter(self.graph.to_undirected()) if nx.is_connected(self.graph.to_undirected()) else 'N/A'
        }
