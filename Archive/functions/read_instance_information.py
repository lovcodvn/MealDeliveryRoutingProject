import os
import pandas as pd

def read_instance_information(instance_dir):
    '''
    Read instance information from the instance directory
    '''

    orders=pd.read_table(os.path.join(instance_dir, 'orders.txt')) # read orders
    restaurants=pd.read_table(os.path.join(instance_dir, 'restaurants.txt')) # read restaurants
    couriers=pd.read_table(os.path.join(instance_dir, 'couriers.txt')) # read couriers
    instanceparams=pd.read_table(os.path.join(instance_dir, 'instance_parameters.txt')) # read instance parameters

    order_locations=pd.DataFrame(data=[orders.order, orders.x, orders.y]).transpose() # create a dataframe for order locations
    order_locations.columns=['id', 'x', 'y'] # set column names for the dataframe for order locations
    
    restaurant_locations=pd.DataFrame(data=[restaurants.restaurant, restaurants.x, restaurants.y]).transpose() # create a dataframe for restaurant locations
    restaurant_locations.columns=['id', 'x', 'y'] # set column names for the dataframe for restaurant locations
    
    courier_locations=pd.DataFrame(data=[couriers.courier, couriers.x, couriers.y]).transpose() # create a dataframe for courier locations
    courier_locations.columns=['id', 'x', 'y'] # set column names for the dataframe for courier locations
    
    locations=pd.concat([order_locations, restaurant_locations, courier_locations]) # concatenate the dataframes for order, restaurant, and courier locations
    locations.set_index('id', inplace=True) # set the index of the dataframe for locations to be the id of the location

    meters_per_minute=instanceparams.at[0,'meters_per_minute'] # get the meters per minute
    pickup_service_minutes=instanceparams.at[0,'pickup service minutes'] # get the pickup service minutes
    dropoff_service_minutes=instanceparams.at[0,'dropoff service minutes'] # get the dropoff service minutes
    target_click_to_door=instanceparams.at[0,'target click-to-door'] # get the target click-to-door
    pay_per_order=instanceparams.at[0,'pay per order'] # get the pay per order
    guaranteed_pay_per_hour=instanceparams.at[0,'guaranteed pay per hour'] # get the guaranteed pay per hour

    return orders,restaurants,couriers,instanceparams,locations, meters_per_minute, pickup_service_minutes, dropoff_service_minutes, \
            target_click_to_door, pay_per_order,\
            guaranteed_pay_per_hour
