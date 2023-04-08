
def remove_reinsert(dr: DeliveryRouting, t: int, r: str, meters_per_minute: int, locations: pd.DataFrame):
    U = dr.orders_by_horizon_interval[t][r]  # Get the orders U(t, r) for the given time t and restaurant r

    for o in U:
        # Remove o from its current route
        original_route, original_position = dr.find_order_route(o)
        if original_route:
            original_route.bundle.pop(original_position)

        # Find route s and position i(s) to re-insert o at minimum cost
        min_cost = float('inf')
        best_route = None
        best_position = None

        for route in dr.routes_by_horizon_interval[t][r]:
            for i in range(len(route.bundle) + 1):
                # Insert o into route s at position i
                route.bundle.insert(i, o)

                # Calculate the new route cost
                new_cost = route.get_route_cost(meters_per_minute, locations)

                # Check if the new cost is less than the current minimum cost
                if new_cost < min_cost:
                    min_cost = new_cost
                    best_route = route
                    best_position = i

                # Remove o from route s at position i
                route.bundle.pop(i)

        # Re-insert o into route s at position i(s)
        if best_route:
            best_route.bundle.insert(best_position, o)

    # Update the routes
    dr.routes_by_horizon_interval[t][r] = [route for route in dr.routes_by_horizon_interval[t][r] if route.bundle]

    return dr