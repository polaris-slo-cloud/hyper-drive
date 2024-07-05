from dataclasses import dataclass
from scheduler.model import AvailableNodes
from scheduler.orchestrator import NodesManager
from scheduler.orchestrator.starrynet import StarryNetClient, StarryNetTimeService
from scheduler import create_default_candidate_nodes_plugin, create_default_commit_plugin, create_default_filter_plugins, create_default_score_plugins, Scheduler, SchedulerConfig, SchedulerPluginsConfig
from scheduler.plugins import ResourcesFitPlugin
from scheduler.plugins.baseline import FirstFitPlugin, RandomSelectionPlugin, RoundRobinPlugin
from starrynet.starrynet.sn_synchronizer import StarryNet
from .nodes_generator import NodesGenerator


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


class ExperimentHelper:

    def __init__(self, random_seed: int = 1):
        self.__random_seed = random_seed


    def init_starrynet(
        self,
        config_path: str,
        sats_per_orbit: int,
        edge_nodes_count: int,
        gs_nodes_count: int,
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
        `sats_per_orbit`: is multiplied by the number of orbits specified in the config file to obtain the total number of satellites.
        `edge_nodes_count`: the total number of edge nodes to generate.
        `gs_nodes_count`: the total number of ground station nodes to generate.
        `edge_node_locations_lat_long`: the locations of edge nodes. If `edge_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `gs_locations_lat_long`: the locations of ground station nodes.  If `gs_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `edge_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        `gs_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        '''
        # By reusing the same seed we ensure that the experiment is reproducible.
        nodes_gen = NodesGenerator(self.__random_seed)

        edge_node_locations_lat_long = self.__extend_locations(nodes_gen, edge_node_locations_lat_long, edge_nodes_count, edge_nodes_location_bounds)
        gs_locations_lat_long = self.__extend_locations(nodes_gen, gs_locations_lat_long, gs_nodes_count, gs_nodes_location_bounds);

        sn = StarryNet(
            configuration_file_path=config_path,
            GS_lat_long=edge_node_locations_lat_long + gs_locations_lat_long,
            hello_interval=1, # hello_interval(s) in OSPF. 1-200 are supported.
            sats_per_orbit_override=sats_per_orbit,
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

        return Experiment(
            sn=sn_setup.sn,
            sn_time_svc=sn_time_svc,
            sn_client=orch_client,
            nodes=nodes,
            nodes_mgr=nodes_mgr,
            scheduler=scheduler,
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
            select_candidate_nodes_plugin=create_default_candidate_nodes_plugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ FirstFitPlugin() ],
            commit_plugin=create_default_commit_plugin(),
        )


    def create_random_scheduler_plugins(self) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=create_default_candidate_nodes_plugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ RandomSelectionPlugin() ],
            commit_plugin=create_default_commit_plugin(),
        )


    def create_roundrobin_scheduler_plugins(self, total_nodes: int) -> SchedulerPluginsConfig:
        return SchedulerPluginsConfig(
            select_candidate_nodes_plugin=create_default_candidate_nodes_plugin(),
            filter_plugins=[ ResourcesFitPlugin() ],
            score_plugins=[ RoundRobinPlugin(total_nodes) ],
            commit_plugin=create_default_commit_plugin(),
        )


    def __extend_locations(self, nodes_gen: NodesGenerator, locs: list[tuple[float, float]], total: int, bounds: tuple[tuple[float, float], tuple[float, float]]) -> list[tuple[float, float]]:
        if len(locs) >= total:
            return locs
        new_locs = nodes_gen.generate_random_locations(total, bounds)
        return locs + new_locs
