from scenarios.util import ExperimentBuilder, NodeCounts, WildfireDetSchedulingQualityExperiment

RESULTS_CSV_PREFIX = 'results'

NODE_COUNTS = [
    NodeCounts(satellites=1000, edge_nodes=100, ground_stations=10),
    NodeCounts(satellites=2000, edge_nodes=200, ground_stations=20),
    NodeCounts(satellites=3000, edge_nodes=300, ground_stations=30),
    NodeCounts(satellites=4000, edge_nodes=400, ground_stations=40),
]

def run_experiment(path_to_scenario_dir: str = '.'):
    exp_builder = ExperimentBuilder()

    for nodes_count in NODE_COUNTS:
        experiment = WildfireDetSchedulingQualityExperiment(nodes_count, f'{path_to_scenario_dir}/../configs')

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
