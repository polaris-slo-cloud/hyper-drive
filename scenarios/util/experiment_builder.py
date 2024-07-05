import math
from dataclasses import dataclass
from scheduler.model import AvailableNodes
from scheduler.orchestrator import NodesManager
from scheduler.orchestrator.starrynet import StarryNetClient, StarryNetTimeService
from scheduler import create_default_candidate_nodes_plugin, create_default_commit_plugin, create_default_filter_plugins, create_default_score_plugins, Scheduler, SchedulerConfig, SchedulerPluginsConfig
from scheduler.plugins import ResourcesFitPlugin, SelectNodesInVicinityPlugin
from scheduler.plugins.baseline import FirstFitPlugin, RandomSelectionPlugin, RoundRobinPlugin, SelectAllNodesPlugin
from starrynet.starrynet.sn_synchronizer import StarryNet
from .nodes_generator import NodesGenerator


@dataclass
class NodeCounts:
    '''
    Configures the number of nodes for an experiment.
    Note that the satellites are an approximate number because the final number is be a multiple of the number of orbital planes.
    '''
    satellites: int
    edge_nodes: int
    ground_stations: int


@dataclass
class StarryNetSetup:
    sn: StarryNet
    satellites_count: int
    total_nodes_count: int
    duration: int
    edge_node_locations_lat_long: list[tuple[float, float]]
    '''All edge node locations, including the randomly generated ones.'''
    gs_locations_lat_long: list[tuple[float, float]]
    '''All ground station locations, including the randomly generated ones.'''


@dataclass
class Experiment:
    sn: StarryNet
    sn_time_svc: StarryNetTimeService
    sn_client: StarryNetClient
    nodes: AvailableNodes
    nodes_mgr: NodesManager
    scheduler: Scheduler
    select_vicinity: SelectNodesInVicinityPlugin
    '''Needed for finding a satellite close to the drone and declaring it as an EO satellite.'''


class ExperimentBuilder:

    def __init__(self, random_seed: int = 1):
        self.__random_seed = random_seed


    def init_starrynet(
        self,
        config_path: str,
        duration_minutes: int,
        node_counts: NodeCounts,
        edge_node_locations_lat_long: list[tuple[float, float]],
        gs_locations_lat_long: list[tuple[float, float]],
        edge_nodes_location_bounds: tuple[tuple[float, float], tuple[float, float]],
        gs_nodes_location_bounds: tuple[tuple[float, float], tuple[float, float]],
    ) -> StarryNetSetup:
        '''
        Creates a StarryNet base setup, which can be used to initialize multiple experiments.
        We separate this step, because it can take a long time to generate satellites trajectories and calculate the latencies for many nodes.
        By separating this step, the generated StarryNet data can be reused for multiple experiments.

        `config_path`: the path of the config.json file.
        `duration_minutes`: the simulated duration of the experiment in minutes.
        `node_counts`: configures the number of nodes in each dimension of the 3D continuum.
        `edge_node_locations_lat_long`: the locations of edge nodes. If `edge_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `gs_locations_lat_long`: the locations of ground station nodes.  If `gs_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `edge_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        `gs_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        '''
        # The configuration file has 72 Starlink orbital planes configured.
        # The total number of satellites is 72 * sats_per_orbit.
        # Even though config.json mentions duration in seconds, we actually interpret the number as minutes
        # and also advance the simulation minute by minute.

        # By reusing the same seed we ensure that the experiment is reproducible.
        nodes_gen = NodesGenerator(self.__random_seed)

        edge_node_locations_lat_long = self.__extend_locations(nodes_gen, edge_node_locations_lat_long, node_counts.edge_nodes, edge_nodes_location_bounds)
        gs_locations_lat_long = self.__extend_locations(nodes_gen, gs_locations_lat_long, node_counts.ground_stations, gs_nodes_location_bounds);

        sn = StarryNet(
            configuration_file_path=config_path,
            GS_lat_long=edge_node_locations_lat_long + gs_locations_lat_long,
            hello_interval=1, # hello_interval(s) in OSPF. 1-200 are supported.
            sats_per_orbit_override=int(math.ceil(node_counts.satellites / 72.0)),
            duration_override=duration_minutes,
        )

        return StarryNetSetup(
            sn=sn,
            satellites_count=sn.constellation_size,
            total_nodes_count=sn.constellation_size + len(edge_node_locations_lat_long) + len(gs_locations_lat_long),
            duration=sn.duration,
            edge_node_locations_lat_long=edge_node_locations_lat_long,
            gs_locations_lat_long=gs_locations_lat_long,
        )


    def init_experiment(self, sn_setup: StarryNetSetup, scheduler_plugins: SchedulerPluginsConfig) -> Experiment:
        '''
        Initializes an experiment with the specified StarryNet setup and its data.
        '''
        # By reusing the same seed we ensure that the experiment is reproducible.
        nodes_gen = NodesGenerator(self.__random_seed)
        sn_time_svc = StarryNetTimeService(sn_setup.duration)

        nodes = nodes_gen.generate_nodes(
            satellites_count=sn_setup.satellites_count,
            edge_node_locs_lat_long=sn_setup.edge_node_locations_lat_long,
            ground_station_locs_lat_long=sn_setup.gs_locations_lat_long,
        )

        nodes_mgr = NodesManager(nodes)
        orch_client = StarryNetClient(nodes_mgr, sn_setup.sn, sn_time_svc)

        scheduler = Scheduler(
            SchedulerConfig(
                select_candidate_nodes_plugin=scheduler_plugins.select_candidate_nodes_plugin,
                filter_plugins=scheduler_plugins.filter_plugins,
                score_plugins=scheduler_plugins.score_plugins,
                commit_plugin=scheduler_plugins.commit_plugin,
                orchestrator_client=orch_client,
            ),
            nodes
        )

        # Needed for finding a satellite that we can declare as EO satellite close to a drone.
        select_vicinity = SelectNodesInVicinityPlugin(
            radius_ground_km=500.0,
            radius_edge_km=100,
            radius_space_km=500,
            ground_nodes_count=0,
            edge_nodes_count=0,
            space_nodes_count=10,
        )

        return Experiment(
            sn=sn_setup.sn,
            sn_time_svc=sn_time_svc,
            sn_client=orch_client,
            nodes=nodes,
            nodes_mgr=nodes_mgr,
            scheduler=scheduler,
            select_vicinity=select_vicinity,
        )


    def create_hyperdrive_scheduler_plugins(self) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=create_default_candidate_nodes_plugin(),
            filter_plugins=create_default_filter_plugins(),
            score_plugins=create_default_score_plugins(),
            commit_plugin=create_default_commit_plugin(),
        )


    def create_firstfit_scheduler_plugins(self) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=SelectAllNodesPlugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ FirstFitPlugin() ],
            commit_plugin=create_default_commit_plugin(),
        )


    def create_random_scheduler_plugins(self) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=SelectAllNodesPlugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ RandomSelectionPlugin() ],
            commit_plugin=create_default_commit_plugin(),
        )


    def create_roundrobin_scheduler_plugins(self, total_nodes: int) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=SelectAllNodesPlugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ RoundRobinPlugin(total_nodes) ],
            commit_plugin=create_default_commit_plugin(),
        )


    def __extend_locations(self, nodes_gen: NodesGenerator, locs: list[tuple[float, float]], total: int, bounds: tuple[tuple[float, float], tuple[float, float]]) -> list[tuple[float, float]]:
        if len(locs) >= total:
            return locs
        new_locs = nodes_gen.generate_random_locations(total, bounds)
        return locs + new_locs
