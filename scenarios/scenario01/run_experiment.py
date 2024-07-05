import math
from typing import cast
from scenarios.util import ExperimentBuilder, create_wildfire_detection_wf, write_results_to_csv
from scheduler import SchedulingResult

RESULTS_CSV = 'results.csv'
NODES_PER_CONTINUUM_DIMENSION = 1000

def run_experiment(path_to_scenario_dir: str = '.'):
    # The configuration file has 72 Starlink orbital planes configured.
    # The total number of satellites is 72 * sats_per_orbit.
    # Even though config.json mentions duration in seconds, we actually interpret the number as minutes
    # and also advance the simulation minute by minute.

    # Locations of the explicitly configured edge nodes.
    # The locations of the rest up to edge_nodes_count is placed randomly within the edge_nodes_location_bounds.
    edge_lat_long = [
        # Drones flying over Mendocino National Forest in California, USA, an area prone to wildfires (https://www.capradio.org/articles/2022/12/15/new-wildfire-risk-map-suggests-california-communities-increasingly-vulnerable/).
        (39.493917, -122.981303),
        (39.525713, -123.000053),
        (39.424175, -122.923482),
        (39.590260, -122.987340),
        (39.530706, -123.102010),
    ]

    # Locations of the explicitly configured ground station nodes.
    # The locations of the rest up to gs_nodes_count is placed randomly within the gs_nodes_location_bounds.
    gs_lat_long = [
        (50.002352, 5.148141), # ESA ground station in Redu, Belgium (part of Estrack core network: https://www.esa.int/Enabling_Support/Operations/ESA_Ground_Stations/Estrack_ESA_s_global_ground_station_network)
        (32.500649, -106.608803), # NASA ground station in White Sands, New Mexico, USA (part of NASA's Near Space network: https://www.nasa.gov/technology/space-comms/near-space-network-complexes/)
    ]

    config_file_path = f'{path_to_scenario_dir}/config.json'
    exp_helper = ExperimentBuilder()
    sn_setup = exp_helper.init_starrynet(
         config_path=config_file_path,
        sats_per_orbit=int(math.ceil(NODES_PER_CONTINUUM_DIMENSION / 72.0)),
        edge_nodes_count=NODES_PER_CONTINUUM_DIMENSION,
        gs_nodes_count=NODES_PER_CONTINUUM_DIMENSION,
        gs_locations_lat_long=gs_lat_long,
        edge_node_locations_lat_long=edge_lat_long,
        edge_nodes_location_bounds=((41.990495, -124.218537), (32.729169, -114.613391)),
        gs_nodes_location_bounds=((90.0, 180.0), (-90.0, -180.0)),
    )
    experiment = exp_helper.init_experiment(
        sn_setup=sn_setup,
        scheduler_plugins=exp_helper.create_hyperdrive_scheduler_plugins(),
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
        # Ensure that the network graph is up to date.
        # Since the graph would normally be updated in the background, we don't want the reading of the delay file and the graph update
        # as a bias in the scheduling time.
        experiment.sn_client.get_network_graph()

        task = wf.get_successors(prev_task[0])[0]
        result = scheduler.schedule(task, wf)
        scheduling_results.append(result)
        if not result.success:
            raise RuntimeError(f'Could not schedule {task.name}. Reason: {result.failure_reason}')
        prev_task[0] = task

    def schedule_and_adjust_eo_sat(curr_time: int):
        schedule_next_task_fn(curr_time)
        # We configure the node of the EO sat now, because we now know which satellites are in the area.
        extract_frames_node_id = int(cast(str, scheduling_results[-1].target_node))
        if scheduling_results[-1].target_node_type != 'SatelliteNode':
            raise SystemError('extract-frames was not scheduled on a satellite')
        eo_sat_node_id = (extract_frames_node_id + 1) % len(experiment.nodes.satellites)
        eo_sat_node = experiment.nodes_mgr.get_node_by_name(f'{eo_sat_node_id}')
        if not eo_sat_node:
            raise SystemError(f'Node {eo_sat_node_id} does not exist.')
        obj_det_task = wf.get_successors(prev_task[0])[0]
        obj_det_task.data_source_slos[0].data_source = eo_sat_node

    sn_time_svc.run_simulation({
        2: schedule_and_adjust_eo_sat,
        4: schedule_next_task_fn,
        10: schedule_next_task_fn,
    })

    print(scheduling_results)
    write_results_to_csv(f'{path_to_scenario_dir}/{RESULTS_CSV}', scheduling_results)


if __name__ == '__main__':
    print('Please import and execute the run_experiment() function from the root directory of the project to ensure that the imports work correctly.')
    exit(1)
