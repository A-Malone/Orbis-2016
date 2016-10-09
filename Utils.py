def path_cost(world, source, obj, next_waypoint, final):
    new_path = world.get_path_length(source, obj) + \
            world.get_path_length(obj, next_waypoint) + \
            world.get_path_length(next_waypoint, final)
    old_path = world.get_path_length(source, final)
    return new_path - old_path