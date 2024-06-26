from scheduler.model import AvailableNodes, CpuArchitecture, GroundStationNode, Location, ResourceType, SatelliteNode
from scheduler.pipeline import FilterPlugin, ScorePlugin, SelectCandidateNodesPlugin
from scheduler.plugins import NetworkQosPlugin, ResourcesFitPlugin, SelectNodesInVicinityPlugin

def create_default_candidate_nodes_plugin() -> SelectCandidateNodesPlugin:
    return SelectNodesInVicinityPlugin()


def create_default_filter_plugins() -> list[FilterPlugin]:
    return [
        ResourcesFitPlugin(),
        NetworkQosPlugin(),
    ]


def create_default_score_plugins() -> list[ScorePlugin]:
    return [
        NetworkQosPlugin(),
    ]


def create_satellites(start_id: int, count: int, resources: dict[ResourceType, int]) -> list[SatelliteNode]:
    nodes: list[SatelliteNode] = []
    for id in range(start_id, start_id + count):
        node = SatelliteNode(
            f'{id}',
            resources,
            CpuArchitecture.ARM64,
        )
        nodes.append(node)
    return nodes


def create_ground_stations(start_id: int, resources: dict[ResourceType, int], locations: list[tuple[float, float]]) -> list[GroundStationNode]:
    nodes: list[GroundStationNode] = []
    id = start_id

    for loc in locations:
        node = GroundStationNode(
            f'{id}',
            resources,
            CpuArchitecture.INTEL64,
            Location(lat=loc[0], long=loc[1], altitude_m=0.0),
        )
        nodes.append(node)
        id += 1
    return nodes


def create_nodes(satellites_count: int, ground_station_locs: list[tuple[float, float]]) -> AvailableNodes:
    return AvailableNodes(
        satellites=create_satellites(
            0,
            satellites_count,
            {
                ResourceType.MEMORY_MIB: 4096,
                ResourceType.MILLI_CPU: 4000,
                ResourceType.BATTERY_MAH: 10000,
            },
        ),
        edge_nodes=[],
        cloud_nodes=[],
        ground_stations=create_ground_stations(
            satellites_count,
            {
                ResourceType.MEMORY_MIB: 32768,
                ResourceType.MILLI_CPU: 32000,
            },
            ground_station_locs,
        )
    )
