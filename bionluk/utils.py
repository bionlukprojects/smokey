import math
import random
from collections import defaultdict

import folium
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

# Constants
DEPOT_COORDINATES = (41.08919085025256, 29.04999926199514)

def haversine_distance(coord1, coord2):
    """
    Calculate the Haversine distance between two latitude-longitude coordinates.
    """
    R = 6371
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_route_length(route):
    return sum(haversine_distance(route[i], route[i + 1]) for i in range(len(route) - 1))

def load_data(file_path):
    return pd.read_excel(file_path)

def create_weekly_schedule_with_dynamic_trucks(data, num_trucks_per_day):
    weekly_schedule = {day: defaultdict(list) for day in range(5)}
    sorted_retailers = data.sort_values(by='FREQUENCY', ascending=False)

    def add_to_schedule(retailer_id, frequency, day_trucks):
        available_days = set(range(5))
        while frequency > 0:
            if not available_days:
                raise ValueError("Cannot schedule more visits than available days.")
            day = random.choice(list(available_days))
            truck_id = random.randint(0, day_trucks[day] - 1)
            weekly_schedule[day][truck_id].append(retailer_id)
            frequency -= 1

            for adjacent_day in [day - 1, day + 1]:
                available_days.discard(adjacent_day)

    for _, row in sorted_retailers.iterrows():
        add_to_schedule(row['OUTLET_ID'], row['FREQUENCY'], num_trucks_per_day)

    return weekly_schedule

def optimize_routes_for_a_day(day_schedule, data, depot_coordinates):
    optimized_routes = {}
    coordinates = data.set_index('OUTLET_ID')[['LATITUDE', 'LONGITUDE']]
    coordinates.loc[-1] = depot_coordinates

    for truck_id, retailers in day_schedule.items():
        if not retailers:
            continue
        route_points = [-1] + retailers + [-1]
        route_coords = coordinates.loc[route_points]
        distances = cdist(route_coords, route_coords, metric='euclidean')

        current_location = 0 
        unvisited = set(range(1, len(route_points) - 1))
        optimized_route = [-1]
        while unvisited:
            next_location = min(unvisited, key=lambda x: distances[current_location, x])
            optimized_route.append(route_points[next_location])
            unvisited.remove(next_location)
            current_location = next_location
        optimized_route.append(-1)
        optimized_routes[truck_id] = optimized_route

    return optimized_routes

def optimize_delivery_routes(data, depot_coordinates, num_trucks_per_day):
    weekly_schedule = create_weekly_schedule_with_dynamic_trucks(data, num_trucks_per_day)
    optimized_routes_weekly = {}
    for day in range(5):
        day_schedule = weekly_schedule[day]
        optimized_routes = optimize_routes_for_a_day(day_schedule, data, depot_coordinates)
        optimized_routes_weekly[day] = optimized_routes
    return optimized_routes_weekly

def transform_routes_to_coordinates(optimized_routes, data):
    """
    Transform the optimized routes into a list of coordinate pairs for each truck's route.
    """
    coordinates_dict = data.set_index('OUTLET_ID')[['LATITUDE', 'LONGITUDE']].to_dict('index')
    routes_coordinates = {}

    for day, trucks_routes in optimized_routes.items():
        day_routes = []
        for truck_id, route in trucks_routes.items():
            truck_route_coords = [
                coordinates_dict[retailer_id] if retailer_id != -1 else {'LATITUDE': DEPOT_COORDINATES[0],
                                                                         'LONGITUDE': DEPOT_COORDINATES[1]} for
                retailer_id in route]
            day_routes.append([(coord['LATITUDE'], coord['LONGITUDE']) for coord in truck_route_coords])
        routes_coordinates[day] = day_routes

    return routes_coordinates

def routes_to_dataframe(transformed_routes):
    """
    Convert the transformed route data into a pandas DataFrame.
    """
    route_data = []
    for day, day_routes in transformed_routes.items():
        for truck_id, route in enumerate(day_routes):
            for step, (lat, lon) in enumerate(route):
                route_data.append(
                    {'Day': day + 1, 'Truck ID': truck_id + 1, 'Step': step + 1, 'Latitude': lat, 'Longitude': lon})

    return pd.DataFrame(route_data)

def save_routes_to_excel(transformed_routes, filename):
    df = routes_to_dataframe(transformed_routes)
    df.to_excel(filename, index=False)
    print(f"Routes saved to {filename}")

def plot_routes_on_map(day_routes, depot_coordinates, day=None, weekly_length=None):
    map_center = depot_coordinates
    folium_map = folium.Map(location=map_center, zoom_start=12)
    total_day_length = 0

    for truck_id, route in enumerate(day_routes):
        route_length = calculate_route_length(route)
        total_day_length += route_length
        line = folium.PolyLine(locations=route, weight=2.5, color=random.choice(['blue', 'green', 'red', 'purple', 'orange']), popup=f'Truck ID: {truck_id + 1}, Length: {route_length:.2f} km')
        folium_map.add_child(line)

    if day is not None and weekly_length is not None:
        folium.Marker(depot_coordinates, popup=(f'Total Route Length for Day {day + 1}: {total_day_length:.2f} km\nTotal Length for the Week: {weekly_length:.2f} km'), icon=folium.Icon(color='black', icon='info-sign')).add_to(folium_map)
        folium_map.save(f"optimized_routes_map_day_{day}.html")
    else:
        folium.Marker(depot_coordinates, popup='Depot', icon=folium.Icon(color='black')).add_to(folium_map)
    if weekly_length is not None:
        # Add a marker at the depot location with the total weekly distance
        folium.Marker(
            depot_coordinates,
            popup=f'Total Distance for the Week: {weekly_length:.2f} km',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(folium_map)
    return folium_map


def main():
    file_path = input('Enter the filename: ')
    data = load_data(file_path)
    truck_availability = get_truck_availability()
    optimized_routes = optimize_delivery_routes(data, DEPOT_COORDINATES, truck_availability)
    transformed_routes = transform_routes_to_coordinates(optimized_routes, data)

    # Ask the user for the specific day
    day = int(input("Enter the day number (1-5): ")) - 1

    # Ensure the day number is within the valid range
    if 0 <= day < 5:
        daily_lengths = [sum(calculate_route_length(route) for route in day_routes) for day_routes in
                         transformed_routes.values()]
        weekly_length = sum(daily_lengths)
        map_with_routes = plot_routes_on_map(transformed_routes[day], DEPOT_COORDINATES, day, weekly_length)
        print(f"Map for Day {day + 1} saved as optimized_routes_map_day_{day}.html")
    else:
        print("Invalid day number. Please enter a number between 1 and 5.")

    save_routes_to_excel(transformed_routes, 'optimized_routes.xlsx')

if __name__ == "__main__":
    main()
