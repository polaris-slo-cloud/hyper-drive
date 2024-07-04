from scenarios.util import ExperimentHelper, create_wildfire_detection_wf, write_results_to_csv
from scheduler import SchedulingResult

RESULTS_CSV = 'results.csv'

def run_experiment(path_to_scenario_dir: str = '.'):
    # The configuration file has 72 Starlink orbital planes configured.
    # The total number of satellites is 72 * sats_per_orbit.

    # Locations of the explicitly configured edge nodes.
    # The locations of the rest up to edge_nodes_count is placed randomly within the edge_nodes_location_bounds.
    edge_lat_long = [
        (39.493917, -122.981303), # Drone flying over Mendocino National Forest in California, USA, an area prone to wildfires (https://www.capradio.org/articles/2022/12/15/new-wildfire-risk-map-suggests-california-communities-increasingly-vulnerable/).
    ]

    # Locations of the explicitly configured ground station nodes.
    # The locations of the rest up to gs_nodes_count is placed randomly within the gs_nodes_location_bounds.
    gs_lat_long = [
        (50.002352, 5.148141), # ESA ground station in Redu, Belgium (part of Estrack core network: https://www.esa.int/Enabling_Support/Operations/ESA_Ground_Stations/Estrack_ESA_s_global_ground_station_network)
        (32.500649, -106.608803), # NASA ground station in White Sands, New Mexico, USA (part of NASA's Near Space network: https://www.nasa.gov/technology/space-comms/near-space-network-complexes/)
    ]

    config_file_path = f'{path_to_scenario_dir}/config.json'
    exp_helper = ExperimentHelper()
    experiment = exp_helper.init_experiment(
        config_path=config_file_path,
        sats_per_orbit=5,
        edge_nodes_count=5,
        gs_nodes_count=5,
        gs_locations_lat_long=gs_lat_long,
        edge_node_locations_lat_long=edge_lat_long,
        edge_nodes_location_bounds=((41.990495, -124.218537), (32.729169, -114.613391)),
        gs_nodes_location_bounds=((90.0, 180.0), (-90.0, -180.0)),
    )
    scheduler = experiment.scheduler
    sn_time_svc = experiment.sn_time_svc

    # StarryNet doesn't support multiple constellations (I think), so we pick the last satellite as our EO satellite.
    eo_sat = experiment.nodes.satellites[-1]

    wf = create_wildfire_detection_wf(eo_sat)
    if not wf.start:
        raise ValueError('Workflow has no start task.')

    scheduling_results: list[SchedulingResult] = []

    # Set up the experiment by assigning the ingest task to the drone node.
    result = scheduler.force_schedule(wf.start, wf, experiment.nodes.edge_nodes[0])
    scheduling_results.append(result)
    prev_task = [ wf.start ]

    def schedule_next_task_fn(curr_time: int):
        task = wf.get_successors(prev_task[0])[0]
        result = scheduler.schedule(task, wf)
        scheduling_results.append(result)
        if not result.success:
            raise RuntimeError(f'Could not schedule {task.name}. Reason: {result.failure_reason}')
        prev_task[0] = task


    sn_time_svc.run_simulation({
        10: schedule_next_task_fn,
        35: schedule_next_task_fn,
        70: schedule_next_task_fn,
    })

    print(scheduling_results)
    write_results_to_csv(f'{path_to_scenario_dir}/{RESULTS_CSV}', scheduling_results)


if __name__ == '__main__':
    run_experiment()
