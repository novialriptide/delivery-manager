def circle_collision(pos, circle_pos, circle_radius):
    dist = pos.distance_squared_to(circle_pos)
    return dist < circle_radius * circle_radius
