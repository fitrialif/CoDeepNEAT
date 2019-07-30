# Most values taken from https://arxiv.org/pdf/1902.06827.pdf in the appendix
# Modules
MODULE_POP_SIZE = 56
MODULE_NODE_MUTATION_CHANCE = 0.08
MODULE_CONN_MUTATION_CHANCE = 0.08
MODULE_TARGET_NUM_SPECIES = 4

# Blueprints
BP_POP_SIZE = 22
BP_NODE_MUTATION_CHANCE = 0.16
BP_CONN_MUTATION_CHANCE = 0.12
BP_TARGET_NUM_SPECIES = 1

# Data augmentations
DA_POP_SIZE = 20
DA_TARGET_NUM_SPECIES = 1

# Number of times to sample blueprints
INDIVIDUALS_TO_EVAL = 75

PERCENT_TO_REPRODUCE = 0.2
ELITE_TO_KEEP = 0.1

MUTATION_TRIES = 100  # number of tries a mutation gets to pick acceptable individual

# Speciation
SPECIES_DISTANCE_THRESH = 1
SPECIES_DISTANCE_THRESH_MOD_MIN = 0.001
SPECIES_DISTANCE_THRESH_MOD_BASE = 0.1
SPECIES_DISTANCE_THRESH_MOD_MAX = 100

# Crossover
EXCESS_COEFFICIENT = 5
DISJOINT_COEFFICIENT = 3
LAYER_SIZE_COEFFICIENT = 7
LAYER_TYPE_COEFFICIENT = 10
