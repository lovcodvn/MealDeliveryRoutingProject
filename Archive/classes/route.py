from functions.travel_time import travel_time

# Import the config file
from config import *
beta = BETA
gamma = GAMMA

class Route(object):
    def __init__(self,bundle : list, restaurant_id : str): 
        '''
        Initialize a route
        '''
        self.bundle = bundle 
        self.restaurant_id = restaurant_id
        self.beta = beta
        self.gamma = gamma
        
    def get_ready_time(self):
        '''
        Get the ready time of the route
        '''
        ready_time = max([o.ready_time for o in self.bundle]) # get the latest ready time of the orders in the route
        
        return ready_time

    def get_total_travel_time(self, meters_per_minute, locations):
        '''
        Get the total travel time of the route from 1st destination to the last destination.
        Do not include pickup service time and drop off service time.
        '''
        travel_points = [self.restaurant_id] + [o.id for o in self.bundle] # get the travel points of the route

        if len(travel_points) == 1:
            return 0 # if there is no order in the route, return 0
        else:
            total_travel_time = 0 # initialize the total travel time
            for i in range(len(travel_points)-1): # for each travel point, calculate the travel time to the next travel point
                total_travel_time += travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations) # add the travel time to the total travel time
            return total_travel_time # return the total travel time

    def get_end_position(self,meters_per_minute,locations):
        '''
        Get the end position of the route
        '''
        end_position = self.bundle[-1].id # return the last order id in the route

        return end_position

    def get_total_service_delay(self, meters_per_minute, locations):
        '''
        Get the total service delay of the route.
        '''
        travel_points = [self.restaurant_id]+ [o.id for o in self.bundle] # get the travel points of the route
        
        if len(travel_points) == 1:
            return 0 # if there is no order in the route, return 0
        else:
            total_service_delay = 0 # initialize the total service delay
            arrival_time_at_cp = self.get_ready_time() # initialize the arrival time at the current travel point
            for i in range(len(travel_points)-1): # for each travel point:
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations)) # calculate the arrival time at the next travel point
                total_service_delay += (arrival_time_at_cp - self.bundle[i].ready_time) # add the service delay to the total service delay
            return total_service_delay # return the total service delay

    def get_total_service_waiting(self, meters_per_minute, locations):
        '''
        Get the total service waiting time of the route.
        Total service waiting time = arrival time at customer place - placement time (ignoring pickup service time and dropoff service time).
        '''
        travel_points = [self.restaurant_id]+[o.id for o in self.bundle] # get the travel points of the route
        
        if len(travel_points) == 1: 
            return 0 # if there is no order in the route, return 0
        else:
            total_service_waiting = 0 # initialize the total service waiting time
            arrival_time_at_cp = self.get_ready_time() # initialize the arrival time at the current travel point
            for i in range(len(travel_points)-1): # for each travel point:
                arrival_time_at_cp += (travel_time(travel_points[i], travel_points[i+1], meters_per_minute, locations)) # calculate the arrival time at the next travel point
                total_service_waiting += (arrival_time_at_cp - self.bundle[i].placement_time) # add the service waiting time to the total service waiting time
            return total_service_waiting

    def route_efficiency(self, meters_per_minute, locations):
        '''
        Calculate the route efficiency: travel time per order
        '''
        route_efficiency = len(self.bundle)/self.get_total_travel_time(meters_per_minute, locations) # calculate the route efficiency as 

        return route_efficiency

    def get_route_cost(self, meters_per_minute, locations):
        '''
        Calculate the route cost
        '''
        route_cost = self.get_total_travel_time(meters_per_minute,locations) + \
            self.beta * self.get_total_service_delay(meters_per_minute,locations) + \
                self.gamma * self.get_total_service_waiting(meters_per_minute,locations) # calculate the route cost as the total travel time + beta * total service delay + gamma * total service waiting
        
        return route_cost
