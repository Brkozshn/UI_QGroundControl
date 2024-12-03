import random
from main import *


def calculate_fitness(path):
    # Fitness function - you can customize this based on your specific requirements
    total_distance = sum(get_distance_metres(path[i], path[i+1]) for i in range(len(path) - 1))
    return 1 / total_distance


def generate_random_path(starting_point, end_point, num_points=100):
    # Generate a random path between starting and end points
    path = [starting_point]
    for _ in range(num_points - 2):
        lat = random.uniform(starting_point.lat, end_point.lat)
        lon = random.uniform(starting_point.lon, end_point.lon)
        alt = starting_point.alt  # Assuming altitudes are the same
        path.append(LocationGlobal(lat, lon, alt))
    path.append(end_point)
    return path


def crossover(parent1, parent2):
    # Single-point crossover
    crossover_point = random.randint(1, len(parent1) - 1)
    child = parent1[:crossover_point] + parent2[crossover_point:]
    return child


def mutate(path, mutation_rate=0.01):
    # Randomly mutate some genes in the path
    for i in range(len(path)):
        if random.random() < mutation_rate:
            path[i].lat += random.uniform(-0.001, 0.001)
            path[i].lon += random.uniform(-0.001, 0.001)
    return path


def optimum_path_planning_algorithm(starting_point, end_point, population_size=100, generations=100):
    # Initialize population
    population = [generate_random_path(starting_point, end_point) for _ in range(population_size)]

    # Evolution loop
    for _ in range(generations):
        # Evaluate fitness of each individual in the population
        fitness_scores = [calculate_fitness(path) for path in population]

        # Select parents for crossover based on fitness
        parents = random.choices(population, weights=fitness_scores, k=2)

        # Apply crossover and mutation to create new generation
        offspring = [mutate(crossover(parents[0], parents[1])) for _ in range(population_size)]

        # Replace old generation with new generation
        population = offspring

    # Select the best path from the final population
    best_path = max(population, key=calculate_fitness)
    return best_path


def determine_circle(starting_point, end_point):
    # Calculate center point
    center_lat = (starting_point.lat + end_point.lat) / 2
    center_lon = (starting_point.lon + end_point.lon) / 2
    center_point = LocationGlobal(center_lat, center_lon, starting_point.alt)  # Assuming altitudes are the same

    # Calculate radius
    radius = get_distance_metres(center_point, starting_point)
    if radius > 15:
        # Generate circle points
        num_points = 100
        circle_points = []
        for i in range(num_points):
            angle = math.radians(i * (360 / num_points))  # Calculate angle in radians
            x = radius * math.cos(angle)  # Calculate X coordinate
            y = radius * math.sin(angle)  # Calculate Y coordinate

            # Calculate the location of the circle point
            circle_location = get_location_metres(center_point, x, y)
            circle_points.append(circle_location)

        # Patrol circumference
        circumference_path = optimum_path_planning_algorithm(starting_point, end_point)

        # Generate paths for concentric circles
        concentric_paths = [circumference_path]  # Add initial path for the circumference
        while radius > 10:  # Adjust this threshold as needed
            radius = radius * 0.95  # Decrease radius
            num_points = int(2 * math.pi * radius)  # Adjust the number of points based on new radius
            circle_path = optimum_path_planning_algorithm(center_point, center_point, num_points=num_points)
            concentric_paths.append(circle_path)
        # Check if the loop terminated because the condition became false
        if radius <= 10:
            land_vehicle()
            raise ValueError("Radius decreased to 10 or less. Terminating loop.")

        # Merge paths
        all_paths = [circumference_path] + concentric_paths
        return all_paths
    else:
        raise ValueError("Radius must be 15 or more. Terminating loop.")
