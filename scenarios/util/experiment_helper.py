from dataclasses import dataclass
from scheduler.model import AvailableNodes
from scheduler.orchestrator import NodesManager
from scheduler.orchestrator.starrynet import StarryNetClient, StarryNetTimeService
from scheduler import create_nodes, create_default_candidate_nodes_plugin, create_default_commit_plugin, create_default_filter_plugins, create_default_score_plugins, Scheduler, SchedulerConfig
from starrynet.starrynet.sn_synchronizer import StarryNet

@dataclass
class Experiment:
    sn: StarryNet
    sn_time_svc: StarryNetTimeService
    nodes: AvailableNodes
    nodes_mgr: NodesManager
    scheduler: Scheduler


def init_experiment(config_path: str, gs_locations_lat_long: list[tuple[float, float]], AS: list[list[int]]) -> Experiment:
    hello_interval = 1  # hello_interval(s) in OSPF. 1-200 are supported.

    sn = StarryNet(config_path, gs_locations_lat_long, hello_interval, AS)
    sn_time_svc = StarryNetTimeService(sn.duration)

    nodes = create_nodes(sn.constellation_size, gs_locations_lat_long)
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
