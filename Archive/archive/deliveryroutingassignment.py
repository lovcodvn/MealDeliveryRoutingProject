from docplex.mp.model import Model
from classes.deliveryrouting import DeliveryRouting


class DeliveryRoutingAssignment(DeliveryRouting):
    def __init__(self, instance_dir: str):
        super().__init__(instance_dir)

    def build_assignment_model(self):
        self.driver_code()  # Generate the bundles

        # Create the model
        model = Model(name="Courier_Bundle_Assignment")

        # Create binary decision variables for each courier and time slot combination
        assignments = {(c.id, t): model.binary_var(name=f"x_{c.id}_{t}")
                    for c in self.couriers for t in self.final_result.keys()}

        # Objective function
        model.minimize(model.sum(assignments[(c.id, t)] * self.final_result[t][0][0].get_route_cost(self.meters_per_minute, self.locations)
                                for c in self.couriers for t in self.final_result.keys()))

        # Constraints
        # Each courier can be assigned to at most one bundle
        for c in self.couriers:
            model.add_constraint(model.sum(assignments[(c.id, t)] for t in self.final_result.keys()) <= 1,
                                ctname=f"courier_{c.id}_assignment_limit")

        # Each bundle can be assigned to at most one courier
        for t in self.final_result.keys():
            model.add_constraint(model.sum(assignments[(c.id, t)] for c in self.couriers) <= 1,
                                ctname=f"bundle_{t}_assignment_limit")

        # Solve the model
        solution = model.solve()

        # Extract the solution
        self.assignment_solution = {}
        if solution:
            for c in self.couriers:
                for t in self.final_result.keys():
                    if solution[assignments[(c.id, t)]] > 0.5:
                        self.assignment_solution[c.id] = self.final_result[t]
        else:
            print("No solution found")
            self.assignment_solution = None

        return self.assignment_solution




