import sys
from scenarios import scenario01

scenarios = {
    'scenario01': scenario01.run_experiment,
}

DEFAULT_SCENARIO = 'scenario01'

# The scenario can be specified as the first command line argument.
# Example: python run-experiment.py scenario01

if __name__ == '__main__':
    scenario_fn = scenarios[DEFAULT_SCENARIO]
    if len(sys.argv) >= 2:
        key = sys.argv[1]
        scenario_fn = scenarios.get(key)
        if not scenario_fn:
            print(f'Unknown scenario: {key}')
            sys.exit(1)

    scenario_fn('./scenarios/scenario01')
