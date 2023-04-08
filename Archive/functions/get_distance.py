def get_distance(source: tuple, destination : tuple) -> float:
    '''
    Get the distance between two points
    '''

    # calculate the distance between the source and the destination
    distance = ((source[1] - destination[1]) ** 2 + (source[0] - destination[0]) ** 2)**0.5

    return distance
