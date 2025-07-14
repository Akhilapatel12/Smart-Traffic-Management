def adjust_green_signal_time(vehicle_count):
    base_green_time = 20  # Shorter base time
    vehicle_multiplier = 1  # Smaller multiplier
    max_green_time = 60  # Lower max time
    green_time = min(base_green_time + (vehicle_count * vehicle_multiplier), max_green_time)
    return green_time