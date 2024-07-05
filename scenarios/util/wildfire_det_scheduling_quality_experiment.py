import math
from typing import cast
from scheduler.model import ResourceType, SatelliteNode
from scheduler import SchedulingResult, SchedulerPluginsConfig
from scheduler.pipeline import SchedulingContext
from scheduler.plugins import SelectNodesInVicinityPlugin
from .workflow_helper import create_wildfire_detection_wf, WildfireDetectionWorkflow
from .results_serializer import write_results_to_csv
from .experiment_builder import Experiment, ExperimentBuilder, NodeCounts, StarryNetSetup

class WildfireDetSchedulingQualityExperiment:

    def __init__(self, node_counts: NodeCounts, path_to_config_dir: str):
        self.__exp_builder = ExperimentBuilder()
        self.__sn_setup = self.__init_sn(node_counts, path_to_config_dir)
        self.total_nodes = self.__sn_setup.total_nodes_count


    def __init_sn(self, node_counts: NodeCounts, path_to_config_dir: str) -> StarryNetSetup:
        print(f'Setting up StarryNet with {node_counts}.')
        config_file_path = f'{path_to_config_dir}/config-72orbits.json'

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

        return self.__exp_builder.init_starrynet(
            config_path=config_file_path,
            duration_minutes=40,
            node_counts=node_counts,
            gs_locations_lat_long=gs_lat_long,
            edge_node_locations_lat_long=edge_lat_long,
            edge_nodes_location_bounds=((41.990495, -124.218537), (32.729169, -114.613391)),
            gs_nodes_location_bounds=((90.0, 180.0), (-90.0, -180.0)),
        )


    def run_scheduling_quality_experiment(self, scheduler_plugins: SchedulerPluginsConfig, results_csv: str):
        experiment = self.__exp_builder.init_experiment(
            sn_setup=self.__sn_setup,
            scheduler_plugins=scheduler_plugins,
        )
        scheduler = experiment.scheduler
        sn_time_svc = experiment.sn_time_svc

        # StarryNet doesn't support multiple constellations (I think), so we pick one of our StarLink satellites as our EO satellite.
        # For now we just pick a temporary one. This will be updated during the experiment.
        eo_sat = experiment.nodes.satellites[-1]

        # Set up five workflows with assigning the ingest tasks to the drone nodes.
        wildfire_workflows: list[WildfireDetectionWorkflow] = []
        for i in range(5):
            wildfire_wf = create_wildfire_detection_wf(eo_sat)
            scheduler.force_schedule(wildfire_wf.ingest_task, wildfire_wf.wf, experiment.nodes.edge_nodes[i])
            wildfire_wf.last_scheduled_task = wildfire_wf.ingest_task
            wildfire_workflows.append(wildfire_wf)

        scheduling_results: list[SchedulingResult] = []

        def schedule_next_task_fn(curr_wildfire_wf: WildfireDetectionWorkflow):
            # Ensure that the network graph is up to date.
            # Since the graph would normally be updated in the background, we don't want the reading of the delay file and the graph update
            # as a bias in the scheduling time.
            experiment.sn_client.get_network_graph()

            task = curr_wildfire_wf.get_next_task()
            result = scheduler.schedule(task, curr_wildfire_wf.wf)
            scheduling_results.append(result)
            if not result.success:
                raise RuntimeError(f'Could not schedule {task.name}. Reason: {result.failure_reason}')
            curr_wildfire_wf.last_scheduled_task = task

        def schedule_and_adjust_eo_sat(curr_wildfire_wf: WildfireDetectionWorkflow):
            schedule_next_task_fn(curr_wildfire_wf)
            # We configure the node of the EO sat now, because we now know which satellites are in the area.
            eo_sat_node = self.__find_eo_satellite(curr_wildfire_wf, experiment, experiment.select_vicinity)
            curr_wildfire_wf.object_det_task.data_source_slos[0].data_source = eo_sat_node

        sn_time_svc.run_simulation({
            2: lambda curr_time: schedule_and_adjust_eo_sat(wildfire_workflows[0]),
            4: lambda curr_time: schedule_next_task_fn(wildfire_workflows[0]),
            8: lambda curr_time: schedule_next_task_fn(wildfire_workflows[0]),

            10: lambda curr_time: schedule_and_adjust_eo_sat(wildfire_workflows[1]),
            12: lambda curr_time: schedule_next_task_fn(wildfire_workflows[1]),
            16: lambda curr_time: schedule_next_task_fn(wildfire_workflows[1]),

            18: lambda curr_time: schedule_and_adjust_eo_sat(wildfire_workflows[2]),
            20: lambda curr_time: schedule_next_task_fn(wildfire_workflows[2]),
            24: lambda curr_time: schedule_next_task_fn(wildfire_workflows[2]),

            26: lambda curr_time: schedule_and_adjust_eo_sat(wildfire_workflows[3]),
            28: lambda curr_time: schedule_next_task_fn(wildfire_workflows[3]),
            32: lambda curr_time: schedule_next_task_fn(wildfire_workflows[3]),

            34: lambda curr_time: schedule_and_adjust_eo_sat(wildfire_workflows[4]),
            36: lambda curr_time: schedule_next_task_fn(wildfire_workflows[4]),
            40: lambda curr_time: schedule_next_task_fn(wildfire_workflows[4]),
        })

        print(scheduling_results)
        write_results_to_csv(results_csv, scheduling_results)


    def __find_eo_satellite(
        self,
        curr_wildfire_wf: WildfireDetectionWorkflow,
        experiment: Experiment,
        select_vicinity: SelectNodesInVicinityPlugin,
    ) -> SatelliteNode:
        '''Finds a satellite close to the ingest task (the drone) and declares it as an EO satellite.'''
        satellites = select_vicinity.select_candidates(
            curr_wildfire_wf.extract_frames_task, # By selecting candidates for extract-frames, we get satellites close to the drone of the ingest task.
            experiment.nodes,
            SchedulingContext(workflow=curr_wildfire_wf.wf, orchestrator=experiment.sn_client),
        )
        if not satellites or len(satellites) == 0:
            raise SystemError('No satellites found in the vicinity of the extract-frames task')
        keys_list = list(satellites.keys())
        satellite = cast(SatelliteNode, satellites[keys_list[-1]])

        # Claim all the resources to avoid having something scheduled on it.
        satellite.resources[ResourceType.MILLI_CPU] = 0
        satellite.resources[ResourceType.MEMORY_MIB] = 0
        return satellite

