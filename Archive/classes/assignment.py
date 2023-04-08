from classes.route import Route

# Import the config file
from config import *
x = X

class Assignment():
    def __init__(self, assign_time:int , restaurant_id:str, courier:object, route:Route):
        '''
        Initialize an assignment
        '''
        self.assign_time = assign_time # the time when the assignment is assigned
        self.restaurant_id = restaurant_id  # each assignment of a bundle has only one corresponding restaurant
        self.pickup_time = 0 # the time when the courier starts to pick up the order
        self.courier = courier # the courier assigned to the assignment
        self.route = route # the route of the assignment
        self.isfinal_flag = 0 # indicate if the assignment is final (can not be updated)
        self.update_time = 0 # the number of times the assignment was updated
        self.departure_time = 0 # the departure time of the courier to the restaurant
        self.departure_location = '' # the last position of the courier before assignment

    def update(self, new_assignment, meters_per_minute, locations):
        '''
        Update the assignment with a new assignment.
        Combine orders in the new assignment with orders in the old assignment.
        '''
        for o in new_assignment.route.bundle: # for each order in the new assignment
            n = len(self.route.bundle) # get the number of orders in the old assignment
            min_route_cost = float('inf') # initialize the minimum route cost
            best_pos = 0 # initialize the best position to insert the order
            
            for pos in range(n+1): # for each position to insert the order
                self.route.bundle.insert(pos, o) # insert the order to the position
                route_cost = self.route.get_route_cost(meters_per_minute, locations) # get the route cost of the new route
                if route_cost < min_route_cost: # if the route cost is smaller than the minimum route cost
                    min_route_cost = route_cost # update the minimum route cost
                    best_pos = pos # update the best position to insert the order
                self.route.bundle.pop(pos) # remove the order from the position
            self.route.bundle.insert(best_pos, o) # insert the order to the best position
        
        if new_assignment.isfinal_flag == 1: # if the new assignment is final (isfinal_flag = 1)
            self.isfinal_flag = 1 # set assignment as final
        else: # if the new assignment is tentative (isfinal_flag = 0)
            if not self.is_no_order_long_ready_time(): # if there is no order that has been ready for x minutes
                self.isfinal_flag = 1 # set assignment as final
            else: # if there is an order that has been ready for x minutes
                self.isfinal_flag = 0 # set assignment as tentative
        
        self.update_time +=1 # update the number of times the assignment is updated
        self.assign_time = new_assignment.assign_time # update the assign time

    def is_no_order_long_ready_time(self, x=X) -> bool:
        '''
        Check that there is no order that has been ready for x minutes
        '''
        for o in self.route.bundle: # for each order in the route
            route_ready_time = self.route.get_ready_time() # get the ready time of the route
            if route_ready_time - o.ready_time >= x: # if the ready time of the route is later than x minutes after the ready time of the order
                return False # then return False
        return True # else return True
