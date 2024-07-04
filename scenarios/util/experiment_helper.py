from dataclasses import dataclass
from scheduler.model import AvailableNodes
from scheduler.orchestrator import NodesManager
from scheduler.orchestrator.starrynet import StarryNetClient, StarryNetTimeService
from scheduler import create_default_candidate_nodes_plugin, create_default_commit_plugin, create_default_filter_plugins, create_default_score_plugins, Scheduler, SchedulerConfig
from starrynet.starrynet.sn_synchronizer import StarryNet
from .nodes_generator import NodesGenerator

@dataclass
class Experiment:
    sn: StarryNet
    sn_time_svc: StarryNetTimeService
    nodes: AvailableNodes
    nodes_mgr: NodesManager
    scheduler: Scheduler


class ExperimentHelper:

    def __init__(self, random_seed: int = 1):
        self.__nodes_gen = NodesGenerator(random_seed)

    def init_experiment(
            self,
            config_path: str,
            sats_per_orbit: int,
            edge_nodes_count: int,
            gs_nodes_count: int,
            edge_node_locations_lat_long: list[tuple[float, float]],
            gs_locations_lat_long: list[tuple[float, float]],
            edge_nodes_location_bounds: tuple[tuple[float, float], tuple[float, float]],
            gs_nodes_location_bounds: tuple[tuple[float, float], tuple[float, float]],
        ) -> Experiment:
        '''
        Initializes an experiment with the specified config file and number of nodes.

        `config_path`: the path of the config.json file.
        `sats_per_orbit`: is multiplied by the number of orbits specified in the config file to obtain the total number of satellites.
        `edge_nodes_count`: the total number of edge nodes to generate.
        `gs_nodes_count`: the total number of ground station nodes to generate.
        `edge_node_locations_lat_long`: the locations of edge nodes. If `edge_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `gs_locations_lat_long`: the locations of ground station nodes.  If `gs_nodes_count` is greater than the number of locations, the rest will be generated randomly.
        `edge_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        `gs_nodes_location_bounds`: the bounds of the region for randomly generated ground station node positions.
        '''

        edge_node_locations_lat_long = self.__extend_locations(edge_node_locations_lat_long, edge_nodes_count, edge_nodes_location_bounds)
        gs_locations_lat_long = self.__extend_locations(gs_locations_lat_long, gs_nodes_count, gs_nodes_location_bounds);

        sn = StarryNet(
            configuration_file_path=config_path,
            GS_lat_long=edge_node_locations_lat_long + gs_locations_lat_long,
            hello_interval=1, # hello_interval(s) in OSPF. 1-200 are supported.
            sats_per_orbit_override=sats_per_orbit,
        )
        sn_time_svc = StarryNetTimeService(sn.duration)

        nodes = self.__nodes_gen.generate_nodes(
            satellites_count=sn.constellation_size,
            edge_node_locs_lat_long=edge_node_locations_lat_long,
            ground_station_locs_lat_long=gs_locations_lat_long,
        )

        nodes_mgr = NodesManager(nodes)
        orch_client = StarryNetClient(nodes_mgr, sn, sn_time_svc)

        scheduler = Scheduler(
            SchedulerConfig(
                select_candidate_nodes_plugin=create_default_candidate_nodes_plugin(),
                filter_plugins=create_default_filter_plugins(),
                score_plugins=create_default_score_plugins(),
                commit_plugin=create_default_commit_plugin(),
                orchestrator_client=orch_client,
            ),
            nodes
        )

        return Experiment(
            sn=sn,
            sn_time_svc=sn_time_svc,
            nodes=nodes,
            nodes_mgr=nodes_mgr,
            scheduler=scheduler,
        )


    def __extend_locations(self, locs: list[tuple[float, float]], total: int, bounds: tuple[tuple[float, float], tuple[float, float]]) -> list[tuple[float, float]]:
        if len(locs) >= total:
            return locs
        new_locs = self.__nodes_gen.generate_random_locations(total, bounds)
        return locs + new_locs
