F_MINUTE = 5 # Every f minutes solves a matching problem to prescribe the next pick-up and delivery assignment for each courier
DELTA_U = 10 # The assignment horizon
BETA = 10 # Control the freshness in the construction of bundles, should be tuned
GAMMA = 10 # Control the click-to-door time in the construction of bundles, should be tuned
OMEGA = 1000 # controlling the undelivered orders
X = 25 # the number of minutes that is considered a long waiting time
COMMITMENT_STRATEGY = 0 # 0: no commitment, 1: commitment
INSTANCE_DIR = './data/5o50t75s1p100'