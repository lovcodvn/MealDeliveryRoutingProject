class Order:
    '''
    Order class
    '''

    def __init__(self, order_information:dict):
        '''
        Initialize an order
        '''

        self.id = order_information.get('order') # order id
        self.destination = (order_information.get('x'), order_information.get('y')) # order location
        self.placement_time = order_information.get('placement_time') # order placement time
        self.restaurant_id = order_information.get('restaurant') # restaurant id
        self.ready_time = order_information.get('ready_time') # order ready time
        self.pickup_time = 0 # order pickup time
        self.dropoff_time = 0 # order dropoff time
        self.courier_id = "" # courier id
        self.assign_time = 0 # assignment time
