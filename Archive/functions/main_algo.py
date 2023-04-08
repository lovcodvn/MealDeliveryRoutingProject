from classes.deliveryrouting import DeliveryRouting
from collections import defaultdict
from docplex.mp.model import Model

def algo(instance_dir):

    dr = DeliveryRouting(instance_dir)  # initialize a delivery routing problem
    dr.get_ready_orders()
    t_list = [*range(0, 24*60+1, dr.f)]
    for t in t_list:
        ready_orders = dr.get_ready_orders_at_t(t)
        idle_couriers = dr.get_idle_courier_at_t(t)
        bundle_size = int(dr.get_bundle_size(t))
        if len(ready_orders)>0:
            list_of_routes_by_restaurant = dr.initialization(t,ready_orders,idle_couriers,bundle_size)
            list_of_routes_by_restaurant = dr.local_search(list_of_routes_by_restaurant)

            
            # create mp model
            m = Model('bundle_assignment')

            list_of_route = [route for r in list_of_routes_by_restaurant for route in r]
            route_index = [i for i in range(len(list_of_route))]
            courier_index = [0]+[j+1 for j in range(len(idle_couriers))]
            route_courier_list = [(i,j) for i in route_index for j in courier_index]
            
            # create variables
            route_courier = m.binary_var_dict(route_courier_list, name='route_courier')
            can_assign = {}
            for i in route_index:
                for j in courier_index: 
                    if j>0:
                        if not dr.can_assign(t, idle_couriers[j-1],list_of_route[i]):
                            can_assign[(i,j)] = 0
                        else:
                            can_assign[(i,j)] = 1
            
            # set objective
            number_of_order_assign_to_pseudo_courier = m.sum(route_courier[i,0] for i in route_index)
            real_pickup_delay = 0
            for i in route_index:
                for j in courier_index:
                    if j>0:
                        route = list_of_route[i]
                        courier = idle_couriers[j-1]
                        arrival_time = courier.next_available_time +\
                            dr.dropoff_service_minutes/2 +\
                            dr.travel_time(courier.position_after_last_assignment,route.restaurant_id) +\
                            dr.pickup_service_minutes/2
                        route_ready_time = route.get_ready_time()
                        real_pickup_delay += max(0,arrival_time-route_ready_time)*route_courier[i,j]
            m.minimize(number_of_order_assign_to_pseudo_courier+real_pickup_delay)
            # constraints
            # each route is assigned to one courier
            for i in route_index:
                m.add_constraint(m.sum(route_courier[i,j] for j in courier_index)==1)
            # each courier is assigned to at most one route
            for j in courier_index:
                if j != 0:
                    m.add_constraint(m.sum(route_courier[i,j] for i in route_index)<=1)
            # check condition can_assign
            for i in route_index:
                for j in courier_index: 
                    if j>0:
                        m.add_constraint(route_courier[i,j]<=can_assign[(i,j)])
            
            # solve model
            solution = m.solve(log_output = False) 

            # assign routes to couriers
            for i in route_index:
                for j in courier_index:
                    if solution.get_value(route_courier[i,j]) == 1:
                        if j != 0:
                            dr.assign_bundle(t, idle_couriers[j-1], list_of_route[i])

    return dr