from collections import defaultdict
import copy
import numpy as np
from typing import Tuple
from classes.assignment import Assignment
from classes.courier import Courier
from classes.order import Order
from classes.route import Route
from functions.read_instance_information import read_instance_information

# Import the config file
from config import *
f_minute = F_MINUTE
commitment_strategy = COMMITMENT_STRATEGY

class DeliveryRouting:
    def __init__(self, instance_dir:str):
        '''
        Initialize a delivery routing problem
        '''

        orders, restaurants, couriers, instanceparams, locations ,\
        self.meters_per_minute, self.pickup_service_minutes, self.dropoff_service_minutes, \
            self.target_click_to_door, self.pay_per_order,\
            self.guaranteed_pay_per_hour = read_instance_information(instance_dir) # read instance information from the instance directory

        # Orders
        self.orders = [Order(order) for order in orders.to_dict(orient = 'records')] # convert orders to Order class
        self.orders = sorted(self.orders, key = lambda x: x.id) # sort orders by id
        self.unassigned_orders = self.copy(self.orders) # unassigned orders
        self.orders_by_horizon_interval = defaultdict(list)

        # Restaurants
        self.restaurants = restaurants # set restaurants in the problem
        
        # Couriers
        self.couriers = [Courier(courier) for courier in couriers.to_dict(orient = 'records')] # convert couriers to Courier class
        
        # Locations
        self.locations = locations
    

    def travel_time(self, origin_id:str, destination_id:str):
        """
        Calculate the travel time between two locations.
        Args:
            origin_id (int): The id of the origin location.
            destination_id (int): The id of the destination location.
        Returns:
            float: The travel time between the origin and destination in minutes.
        """

        dist = np.sqrt((self.locations.at[destination_id, 'x'] - self.locations.at[origin_id, 'x'])**2\
                    + (self.locations.at[destination_id, 'y'] - self.locations.at[origin_id, 'y'])**2) # calculate the distance between the origin and the destination
        
        tt = np.ceil(dist/self.meters_per_minute) # calculate the travel time between the origin and the destination
        
        return tt

    def copy(self, x):
        '''
        This function is used to copy a list of objects
        '''
        
        return copy.deepcopy(x)

    def get_ready_orders(self) -> dict:
        '''
        This function return orders which have ready time fall into the corresponding horizon.
        This function should be run only once.
        '''
        t_list = [*range(0, 24*60+1, self.f)] # initiate the starting time of each interval
        
        for i in range(1, len(t_list)): # loop through each interval
            for o in self.orders: # loop through each order
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time < t_list[i] + self.delta_u: # if the order placement time is within the interval and the order is ready within the assignemnt horizon
                    self.orders_by_horizon_interval[t_list[i]].append(o) # append the order to the corresponding horizon
                if o.placement_time < t_list[i] and o.placement_time >= t_list[i-1] and o.ready_time >= t_list[i] + self.delta_u: # if the order placement time is within the interval but the order is ready after the assignemnt horizon
                    self.orders_by_horizon_interval[t_list[i] + self.f * np.ceil((o.ready_time - (t_list[i] + self.delta_u))/self.f)].append(o) # append the order to a future horizon in which the order is ready.

    def get_ready_orders_at_t(self, t):
        '''
        This function return orders which have ready time fall into the corresponding horizon.
        '''

        return self.orders_by_horizon_interval[t]

    def get_idle_courier_at_t(self, t):
        '''
        Get idle couriers at time t
        '''
        idle_courier = [] # initiate a list of idle couriers

        for c in self.couriers: # loop through each courier
            if c.next_available_time < t + self.delta_u and c.next_available_time < c.off_time : # if the courier is next available within the assignment horizon and the courier is not off duty
                idle_courier.append(c) # append the courier to the list of idle couriers
        return idle_courier # return the list of idle couriers

    def get_bundle_size(self, t) -> int :
        '''
        Get the bundle size at time t
        '''
        number_of_orders = len(self.get_ready_orders_at_t(t)) # get the number of orders ready at time t
        number_of_couriers = len(self.get_idle_courier_at_t(t)) # get the number of idle couriers at time t
        
        if number_of_couriers == 0: # if there are no idle couriers
            bundle_size = 2 # default value of bundle size
        else:
            bundle_size = np.ceil(number_of_orders/number_of_couriers) # otherwise the bundle size is the number of orders divided by the number of idle couriers
        return bundle_size # return the bundle size

    def can_assign(self, t, courier, route : Route) -> bool:
        '''
        Check if a courier can take a bundle
        '''

        route_ready_time = route.get_ready_time() # get the ready time of the bundle
        
        if route_ready_time < courier.on_time: # if the ready time of the bundle is before the courier's on duty time
            return False # the courier cannot take the bundle
        if route_ready_time> courier.off_time: # if the ready time of the bundle is after the courier's off duty time
            return False # the courier cannot take the bundle
        
        arrival_time = max(t, courier.next_available_time) +\
                        self.dropoff_service_minutes/2 +\
                         self.travel_time(courier.position_after_last_assignment, route.restaurant_id) +\
                          self.pickup_service_minutes/2 # calculate the arrival time of the courier to the bundle's restaurant as the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2, the travel time to the restaurant, and the pickup service time divided by 2
        
        if arrival_time > courier.off_time: # if the arrival time is after the courier's off duty time
            return False # the courier cannot take the bundle
        
        if len(courier.assignments) > 0: # if the courier has taken at least one bundle
            if courier.assignments[-1].isfinal_flag == 0: # if the last bundle the courier took is not final
                if courier.assignments[-1].restaurant_id != route.restaurant_id: # if the last bundle the courier took is not from the same restaurant as the current bundle
                    return False # the courier cannot take the bundle
        
        return True # otherwise the courier can take the bundle

    def assign_bundle(self, t:int, courier:Courier, route:Route):
        '''
        Assign a bundle to a courier
        '''

        arrival_time = max(t, courier.next_available_time) +\
                        self.dropoff_service_minutes/2 +\
                         self.travel_time(courier.position_after_last_assignment, route.restaurant_id) +\
                          self.pickup_service_minutes/2 # calculate the arrival time of the courier to the bundle's restaurant as the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2, the travel time to the restaurant, and the pickup service time divided by 2

        route_ready_time = route.get_ready_time() # get the ready time of the bundle
        pickup_time = max(arrival_time, route_ready_time) # calculate the pickup time as the maximum of the arrival time and the ready time of the bundle
        assignment = Assignment(t, route.restaurant_id, courier, route) # create an assignment object
        
        assignment.pickup_time = pickup_time # set the pickup time of the assignment to the pickup time calculated above
        assignment.departure_time = max(t, courier.next_available_time) + self.dropoff_service_minutes/2 # set the departure time of the assignment to the maximum of the current time and the courier's next available time plus the dropoff service time divided by 2
        assignment.departure_location = courier.position_after_last_assignment # set the departure location of the assignment to the courier's position after the last assignment
        
        for i, order in enumerate(route.bundle): # loop through each order in the bundle
            order.pickup_time = pickup_time # set the pickup time of the order to the pickup time calculated above
            order.assign_time = t # set the assign time of the order to the current time
            order.courier_id = courier.id # set the courier id of the order to the courier's id
            
            if i == 0: # if the order is the first order in the bundle
                order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                        self.travel_time(route.restaurant_id, order.id) +\
                                        self.dropoff_service_minutes/2 # set the dropoff time of the order to the pickup time plus the pickup service time divided by 2 plus the travel time from the restaurant to the order, and the dropoff service time divided by 2 
            else: # if the order is not the first order in the bundle
                order.dropoff_time = route.bundle[i-1].dropoff_time +\
                                        self.dropoff_service_minutes/2 +\
                                        self.travel_time(route.bundle[i-1].id, order.id) +\
                                        self.dropoff_service_minutes/2 # set the dropoff time of the order to the dropoff time of the previous order plus the dropoff service time divided by 2 plus the travel time from the previous order to the current order, and the dropoff service time divided by 2

        ## Commitment strategy
        # If the courier, c, can reach the restaurant, r, before time t + f, and all orders in the bundle, b, are estimated to be ready by t + f,
        # Then make a final commitment of the courier to the bundle - instruct the courer to travel to the restaurant, pick up and deliver the orders in the bundle.

        if (arrival_time <= t + f_minute and route_ready_time <= t + f_minute) or\
           (route_ready_time <= t + f_minute and route_ready_time <= arrival_time): # if the arrival time is before the current time plus f minutes and the ready time of the bundle is before the current time plus f minutes and the ready time of the bundle is before the arrival time
            
            assignment.isfinal_flag = 1 # set the isfinal flag of the assignment to 1
            
            if len(courier.assignments) > 0: # if the courier has taken at least one bundle
                if courier.assignments[-1].isfinal_flag == 0: # if the last assignment is not final

                    courier.assignments[-1].update(assignment, self.meters_per_minute, self.locations) # update the last assignment of the courier with the new assignment
                    courier.assignments[-1].pickup_time = max(arrival_time, courier.assignments[-1].route.get_ready_time()) # set the pickup time of the last assignment to the maximum of the arrival time and the ready time of the bundle
                    courier.next_available_time = courier.assignments[-1].pickup_time + self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                     self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle) - 1) +\
                                                      self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                    
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute, self.locations) # set the position after the last assignment of the courier to the end position of the bundle
                    
                    for i, order in enumerate(courier.assignments[-1].route.bundle): # loop through each order in the bundle
                        order.pickup_time = pickup_time # set the pickup time of the order to the pickup time calculated above
                        order.courier_id = courier.id  # set the courier id of the order to the courier's id
                        
                        if i == 0: # if the order is the first order in the bundle
                            order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].restaurant_id, order.id) +\
                                                    self.dropoff_service_minutes/2 # set the dropoff time of the order to the pickup time plus the pickup service time divided by 2 plus the travel time from the restaurant to the order, and the dropoff service time divided by 2
                        else: # if the order is not the first order in the bundle
                            order.dropoff_time = courier.assignments[-1].route.bundle[i-1].dropoff_time +\
                                                    self.dropoff_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].route.bundle[i-1].id, order.id) +\
                                                    self.dropoff_service_minutes/2 # set the dropoff time of the order to the dropoff time of the previous order plus the dropoff service time divided by 2 plus the travel time from the previous order to the current order, and the dropoff service time divided by 2
                
                else: # if the last assignment is final
                    courier.assignments.append(assignment) # append the assignment to the courier's assignments
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute, self.locations) +\
                                                    self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle) -1) +\
                                                    self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations) # set the position after the last assignment of the courier to the end position of the bundle
            
            else: # if the courier has not taken any bundles
                courier.assignments.append(assignment) # append the assignment to the courier's assignments
                courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute, self.locations) +\
                                                    self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle) -1) +\
                                                    self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations) # set the position after the last assignment of the courier to the end position of the bundle
        
        else: # if the courier is not available
            if commitment_strategy == 0: # if the commitment strategy is 0
                assignment.isfinal_flag = 1 # set the isfinal flag of the assignment to 1
            else: # if the commitment strategy is not 0
                assignment.isfinal_flag = 0 # set the isfinal flag of the assignment to 0
            
            if len(courier.assignments) > 0: # if the courier has taken at least one bundle
                if courier.assignments[-1].isfinal_flag == 0: # if the last assignment is not final
                    courier.assignments[-1].update(assignment, self.meters_per_minute, self.locations) # update the last assignment of the courier
                    courier.assignments[-1].pickup_time = max(arrival_time, courier.assignments[-1].route.get_ready_time()) # set the pickup time of the last assignment of the courier to the maximum of the arrival time and the ready time of the bundle
                    
                    if courier.assignments[-1].isfinal_flag == 1: # if the last assignment is final
                        courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute,self.locations) +\
                                                        self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle) -1) +\
                                                        self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                        courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations) # set the position after the last assignment of the courier to the end position of the bundle
                    else: # if the last assignment is not final
                        pass # do nothing
                    
                    for i, order in enumerate(courier.assignments[-1].route.bundle): # for each order in the bundle
                        order.pickup_time = pickup_time # set the pickup time of the order to the pickup time
                        order.courier_id = courier.id # set the courier id of the order to the courier id
                        
                        if i == 0: # if the order is the first order in the bundle
                            order.dropoff_time = pickup_time + self.pickup_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].restaurant_id, order.id) +\
                                                    self.dropoff_service_minutes/2 # set the dropoff time of the order to the pickup time plus the pickup service time divided by 2 plus the travel time from the restaurant to the order, and the dropoff service time divided by 2
                        else: # if the order is not the first order in the bundle
                            order.dropoff_time = courier.assignments[-1].route.bundle[i-1].dropoff_time +\
                                                    self.dropoff_service_minutes/2 +\
                                                    self.travel_time(courier.assignments[-1].route.bundle[i-1].id, order.id) +\
                                                    self.dropoff_service_minutes/2 # set the dropoff time of the order to the dropoff time of the previous order plus the dropoff service time divided by 2 plus the travel time from the previous order to the current order, and the dropoff service time divided by 2
                
                else: # if the last assignment can not be updated
                    courier.assignments.append(assignment) # append the assignment to the courier's assignments
                    if courier.assignments[-1].isfinal_flag == 1: # if the last assignment is final
                        courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                        courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute, self.locations) +\
                                                        self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle)-1) +\
                                                        self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                        courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute, self.locations) # set the position after the last assignment of the courier to the end position of the bundle
            else: 
                courier.assignments.append(assignment) # append the assignment to the courier's assignments
                if courier.assignments[-1].isfinal_flag == 1: # if the last assignment is final
                    courier.next_available_time = courier.assignments[-1].pickup_time +  self.pickup_service_minutes/2 +\
                                                    courier.assignments[-1].route.get_total_travel_time(self.meters_per_minute, self.locations) +\
                                                    self.dropoff_service_minutes*(len(courier.assignments[-1].route.bundle) -1) +\
                                                    self.dropoff_service_minutes/2 # set the next available time of the courier to the pickup time plus the pickup service time divided by 2 plus the total travel time of the bundle, and the dropoff service time multiplied by the number of orders in the bundle minus 1, and the dropoff service time divided by 2
                    courier.position_after_last_assignment = courier.assignments[-1].route.get_end_position(self.meters_per_minute,self.locations) # set the position after the last assignment of the courier to the end position of the bundle

    def initialization(self, t:int, ready_orders:list, idle_couriers:list, bundle_size:int):
        '''
        This function is used to initialize the assignment of orders to couriers at the beginning of the simulation.
        '''

        list_of_routes_by_restaurant = [] # Initiate an empty list of routes by restaurant

        if not ready_orders: # if there are no ready orders
            return  list_of_routes_by_restaurant # return the empty list of routes by restaurant
        else: # if there are ready orders
            for r_id in self.restaurants['restaurant']: # for each restaurant
                r_order= [] # Initiate an empty list of orders for the restaurant
                
                for o in ready_orders: # for each order
                    if o.restaurant_id == r_id: # if the order is from the restaurant
                        r_order.append(o) # append the order to the list of orders for the restaurant
                
                number_of_bundle = int(np.ceil(len(r_order)/bundle_size)) # get the number of bundles for the restaurant by rounding up the number of orders divided by the bundle size
                set_of_bundles = [[] for _ in range(number_of_bundle)] # Initiate a list of empty bundles for the restaurant
                
                # Assign orders into bundels:
                for o in r_order: # for each order
                    min_cost_increase = float('inf') # Initiate the minimum cost increase to infinity

                    for i in range(number_of_bundle): # for each bundle
                        n = len(set_of_bundles[i]) # get the number of orders in the bundle
                        if n + 1<= bundle_size: # if the number of orders in the bundle plus 1 is less than or equal to the bundle size
                            min_route_cost = float('inf') # Initiate the minimum route cost to infinity
                            for pos in range(n+1): # for each position in the bundle
                                set_of_bundles[i].insert(pos, o) # insert the order into the bundle at the position 
                                if Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) < min_route_cost: # if the route cost of the bundle is less than the minimum route cost
                                    min_route_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) # set the minimum route cost to the route cost of the bundle
                                    best_pos = pos # set the best position to the position
                                set_of_bundles[i].pop(pos) # remove the order from the bundle at the position  
                        else: # if the number of orders in the bundle plus 1 is greater than the bundle size
                            min_route_cost = float('inf') # Initiate the minimum route cost to infinity
                            
                            for pos in range(n+1): # for each position in the bundle
                                set_of_bundles[i].insert(pos,o) # insert the order into the bundle at the position
                                if Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) < min_route_cost: # if the route cost of the bundle is less than the minimum route cost
                                    min_route_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) # set the minimum route cost to the route cost of the bundle
                                    best_pos = pos # set the best position to the position
                                set_of_bundles[i].pop(pos) # remove the order from the bundle at the position
                            
                            current_efficiency = n/Route(set_of_bundles[i], r_id).get_total_travel_time(self.meters_per_minute, self.locations) # get the current efficiency of the bundle
                            set_of_bundles[i].insert(best_pos, o) # insert the order into the bundle at the best position
                            new_efficiency = (n+1)/Route(set_of_bundles[i], r_id).get_total_travel_time(self.meters_per_minute, self.locations) # get the new efficiency of the bundle

                            if current_efficiency < new_efficiency: # if the current efficiency is less than the new efficiency
                                set_of_bundles[i].pop(best_pos) # remove the order from the bundle at the best position
                            else: # if the current efficiency is greater than or equal to the new efficiency
                                set_of_bundles[i].pop(best_pos) # remove the order from the bundle at the best position
                                continue # continue to the next bundle

                        current_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) # get the current cost of the bundle
                        set_of_bundles[i].insert(best_pos, o) # insert the order into the bundle at the best position
                        new_cost = Route(set_of_bundles[i], r_id).get_route_cost(self.meters_per_minute, self.locations) # get the new cost of the bundle
                        cost_increase = new_cost - current_cost # get the cost increase of the bundle
                        
                        if cost_increase < min_cost_increase: # if the cost increase of the bundle is less than the minimum cost increase
                            min_cost_increase = cost_increase # set the minimum cost increase to the cost increase of the bundle
                            best_i = i # set the best bundle to the bundle
                            best_i_pos = best_pos # set the best position to the best position
                        set_of_bundles[i].pop(best_pos) # remove the order from the bundle at the best position

                    set_of_bundles[best_i].insert(best_i_pos, o) # insert the order into the best bundle at the best position
                
                set_of_bundles = [Route(bundle, r_id) for bundle in set_of_bundles] # convert the list of bundles into a list of routes
                
                if set_of_bundles: # if the list of routes is not empty
                    list_of_routes_by_restaurant.append(set_of_bundles) # append the list of routes to the list of routes by restaurant

            return list_of_routes_by_restaurant 
        

        ### Local Search ###

        def get_restaurant_cost(self, res:list):
            '''
            Get the total cost of a restaurant
            '''
            res_cost = 0 # Initiate the cost of the restaurant
            
            for route in res: # for each route of the restaurant
                res_cost += route.get_route_cost(self.meters_per_minute, self.locations) # add the cost of the route to the total cost of the restaurant
            
            return res_cost
        
        def get_total_restaurant_cost(self, list_of_routes_by_restaurant:list):
            '''
            Get the total cost of all restaurants
            '''
            total_res_cost = 0 # Initiate the total cost of all restaurants
            
            for res in list_of_routes_by_restaurant: # for each restaurant
                for route in res: # for each route of the restaurant
                    total_res_cost += route.get_route_cost(self.meters_per_minute, self.locations) # add the cost of the route to the total cost of all restaurants
            
            return total_res_cost

        def local_search(self, list_of_routes_by_restaurant):
            '''
            Perform local search on the list of routes by restaurant
            '''
            current_total_res_cost = self.get_total_restaurant_cost(list_of_routes_by_restaurant)

            for res in list_of_routes_by_restaurant: # for each restaurant
                current_cost = self.get_restaurant_cost(res) # get the current cost of the restaurant
                
                for route1 in res: # for each route of the restaurant
                    route1_copy = [o for o in route1.bundle] # make a copy of the orders in the route
                    for o in route1_copy: # for each order in the route
                        best_route = route1 # initiate the best route to be the current route
                        best_pos = route1.bundle.index(o) # initiate the best position to be the current position
                        route1.bundle.remove(o) # remove the order from the route

                        for route2 in res: # for each route of the restaurant
                            for j in range(len(route2.bundle)+1): # for each position in the route

                                route2.bundle.insert(j,o) # insert the order at position j
                                new_cost = self.get_restaurant_cost(res) # get the new cost of the restaurant
                                
                                if new_cost < current_cost: # if the new cost is less than the current cost 
                                    current_cost = new_cost # update the current cost
                                    best_route = route2 # update the best route
                                    best_pos = j # update the best position

                                route2.bundle.pop(j) # remove the order from the route

                        best_route.bundle.insert(best_pos,o) # insert the order at the best position
            
            for res_index in range(len(list_of_routes_by_restaurant)): # for each restaurant
                list_of_routes_by_restaurant[res_index] = [route for route in list_of_routes_by_restaurant[res_index] if len(route.bundle)!= 0] # remove empty routes
                
            new_total_res_cost = self.get_total_restaurant_cost(list_of_routes_by_restaurant) # get the new total cost of all restaurants
            
            return list_of_routes_by_restaurant