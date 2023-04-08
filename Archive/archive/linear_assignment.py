import numpy as np
from scipy.optimize import linear_sum_assignment

def linear_assignment_model(dr: DeliveryRouting, t: int, theta: float, meters_per_minute: int, locations: pd.DataFrame):
    bundles = dr.get_bundles(t)
    couriers = dr.get_couriers(t)
    
    # Initialize the cost matrix
    cost_matrix = np.zeros((len(bundles), len(couriers)))

    for s_idx, bundle in enumerate(bundles):
        N_s = len(bundle.orders)
        for d_idx, courier in enumerate(couriers):
            # Calculate pick-up and drop-off times
            pickup_time = dr.calculate_pickup_time(bundle, courier, meters_per_minute, locations)
            dropoff_times = [dr.calculate_dropoff_time(order, bundle, courier, meters_per_minute, locations) for order in bundle.orders]

            # Calculate cost for each (s, d) pair
            max_dropoff_time = max(dropoff_times)
            max_ready_time = max([order.ready_time for order in bundle.orders])
            cost = (N_s / (max_dropoff_time - courier.start_time)) - theta * (pickup_time - max_ready_time)
            cost_matrix[s_idx, d_idx] = -cost  # Negate the cost because the linear_sum_assignment function minimizes the sum

    # Solve the linear assignment problem
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Extract the assignments
    assignments = [(bundles[row], couriers[col]) for row, col in zip(row_ind, col_ind)]

    return assignments