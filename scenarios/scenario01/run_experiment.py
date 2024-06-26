from scenarios.util import init_experiment, create_wildfire_detection_wf
from scheduler.model import Task
from scheduler import SchedulingResult


def run_experiment(path_to_scenario_dir: str = '.'):
    # Starlink 5*5: 25 satellite nodes, 2 ground stations.
    # The node index sequence is: 25 satellites, 2 ground stations.
    # In this example, 25 satellites and 2 ground stations are one AS.

    AS = [[1, 27]]  # Node #1 to Node #27 are within the same AS.
    gs_lat_long = [
        (50.002352, 5.148141), # ESA ground station in Redu, Belgium (part of Estrack core network: https://www.esa.int/Enabling_Support/Operations/ESA_Ground_Stations/Estrack_ESA_s_global_ground_station_network)
        (32.500649, -106.608803), # NASA ground station in White Sands, New Mexico, USA (part of NASA's Near Space network: https://www.nasa.gov/technology/space-comms/near-space-network-complexes/)

        (39.493917, -122.981303), # Drone flying over Mendocino National Forest in California, USA, an area prone to wildfires (https://www.capradio.org/articles/2022/12/15/new-wildfire-risk-map-suggests-california-communities-increasingly-vulnerable/).
    ]
    config_file_path = f'{path_to_scenario_dir}/config.json'
    experiment = init_experiment(config_file_path, gs_lat_long, AS)
    scheduler = experiment.scheduler
    sn_time_svc = experiment.sn_time_svc

    # StarryNet doesn't support multiple constellations (I think), so we pick the last satellite as our EO satellite.
    eo_sat = experiment.nodes.satellites[-1]

    wf = create_wildfire_detection_wf(eo_sat)
    if not wf.start:
        raise ValueError('Workflow has no start task.')

    scheduling_results: list[SchedulingResult] = []

    # Set up the experiment by assigning the ingest task to the drone node.
    result = scheduler.force_schedule(wf.start, wf, experiment.nodes.ground_stations[-1])
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


if __name__ == '__main__':
    run_experiment()
