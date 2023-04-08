import numpy as np
import pandas as pd

def travel_time(origin_id : str, destination_id : str , meters_per_minute : int, locations : pd.DataFrame):
    """
    Calculate the travel time between two locations.
    Args:
        origin_id (int): The id of the origin location.
        destination_id (int): The id of the destination location.
        meters_per_minute (float): The average speed of the vehicle in meters per minute.
        locations (DataFrame): The DataFrame containing the locations.

    Returns:
        float: The travel time between the origin and destination in minutes.
    :param locations:
    """

    dist = np.sqrt((locations.at[destination_id, 'x'] - locations.at[origin_id, 'x'])**2\
                + (locations.at[destination_id, 'y'] - locations.at[origin_id, 'y'])**2) # calculate the distance between the origin and the destination
    
    tt = np.ceil(dist/meters_per_minute) # calculate the travel time between the origin and the destination
    
    return tt
