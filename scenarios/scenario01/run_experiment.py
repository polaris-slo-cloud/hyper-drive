from scenarios.util import ExperimentBuilder, WildfireDetSchedulingQualityExperiment

RESULTS_CSV_PREFIX = 'results-'

NODES_PER_CONTINUUM_DIMENSION = [
    400,
    600,
    800,
    1000,
]

def run_experiment(path_to_scenario_dir: str = '.'):
    exp_builder = ExperimentBuilder()

    for nodes_per_dimension in NODES_PER_CONTINUUM_DIMENSION:
        experiment = WildfireDetSchedulingQualityExperiment(nodes_per_dimension, f'{path_to_scenario_dir}/../configs')

        print('Executing experiment with HyperDrive')
        experiment.run_scheduling_quality_experiment(
            exp_builder.create_hyperdrive_scheduler_plugins(),
            f'{path_to_scenario_dir}/results/{RESULTS_CSV_PREFIX}-{experiment.total_nodes}-hyperdrive.csv',
        )

        print('Executing experiment with Greedy FirstFit')
        experiment.run_scheduling_quality_experiment(
            exp_builder.create_firstfit_scheduler_plugins(),
            f'{path_to_scenario_dir}/results/{RESULTS_CSV_PREFIX}-{experiment.total_nodes}-firstfit.csv',
        )

        print('Executing experiment with Random scheduler')
        experiment.run_scheduling_quality_experiment(
            exp_builder.create_random_scheduler_plugins(),
            f'{path_to_scenario_dir}/results/{RESULTS_CSV_PREFIX}-{experiment.total_nodes}-random.csv',
        )

        print('Executing experiment with RoundRobin scheduler')
        experiment.run_scheduling_quality_experiment(
            exp_builder.create_roundrobin_scheduler_plugins(experiment.total_nodes),
            f'{path_to_scenario_dir}/results/{RESULTS_CSV_PREFIX}-{experiment.total_nodes}-roundrobin.csv',
        )


if __name__ == '__main__':
    print('Please import and execute the run_experiment() function from the root directory of the project to ensure that the imports work correctly.')
    exit(1)
