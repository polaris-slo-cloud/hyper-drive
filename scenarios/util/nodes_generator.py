from random import Random
from scheduler.model import AvailableNodes, CpuArchitecture, EdgeNode, GroundStationNode, HeatInfo, Location, ResourceType, SatelliteNode

class NodesGenerator:

    def __init__(self, seed: int):
        self.__random = Random(seed)


    def generate_satellites(
            self,
            start_id: int,
            count: int,
            resources: list[dict[ResourceType, int]],
            heat_configs: list[HeatInfo],
        ) -> list[SatelliteNode]:
        '''
        Generates `count` satellite nodes. The resources for each node are picked randomly from the resources list.
        '''

        nodes: list[SatelliteNode] = []
        for id in range(start_id, start_id + count):
            node = SatelliteNode(
                f'{id}',
                self.__random.choice(resources),
                CpuArchitecture.ARM64,
                self.__random.choice(heat_configs),
            )
            nodes.append(node)
        return nodes


    def generate_edge_nodes(
            self,
            start_id: int,
            resources: list[dict[ResourceType, int]],
            locations: list[tuple[float, float]],
        ) -> list[EdgeNode]:
        '''
        Generates `len(locations)` edge nodes. The resources for each node are picked randomly from the resources list.
        '''

        nodes: list[EdgeNode] = []
        id = start_id

        for loc in locations:
            node = EdgeNode(
                f'{id}',
                self.__random.choice(resources),
                CpuArchitecture.ARM64,
                Location(lat=loc[0], long=loc[1], altitude_m=0.0),
            )
            nodes.append(node)
            id += 1
        return nodes


    def generate_ground_stations(
            self,
            start_id: int,
            resources: list[dict[ResourceType, int]],
            locations: list[tuple[float, float]],
        ) -> list[GroundStationNode]:
        '''
        Generates `len(locations)` ground station nodes. The resources for each node are picked randomly from the resources list.
        '''

        nodes: list[GroundStationNode] = []
        id = start_id

        for loc in locations:
            node = GroundStationNode(
                f'{id}',
                self.__random.choice(resources),
                CpuArchitecture.INTEL64,
                Location(lat=loc[0], long=loc[1], altitude_m=0.0),
            )
            nodes.append(node)
            id += 1
        return nodes


    def generate_nodes(
            self,
            satellites_count: int,
            edge_node_locs: list[tuple[float, float]],
            ground_station_locs: list[tuple[float, float]],
        ) -> AvailableNodes:
        return AvailableNodes(
            satellites=self.generate_satellites(
                0,
                satellites_count,
                [
                    {
                        ResourceType.MEMORY_MIB: 4096,
                        ResourceType.MILLI_CPU: 4000,
                        ResourceType.BATTERY_MAH: 10000,
                    }
                ],
                [
                    HeatInfo(
                        max_temp_C=75.0,
                        recommended_high_temp_C=65.0,
                        temperature_C=45.0,
                        radiated_heat_per_minute_C=0.1,
                        temp_inc_per_cpu_minute_C=1.0,
                        mocked_max_orbit_base_temp_C=55.0,
                    ),
                    HeatInfo(
                        max_temp_C=75.0,
                        recommended_high_temp_C=65.0,
                        temperature_C=45.0,
                        radiated_heat_per_minute_C=0.1,
                        temp_inc_per_cpu_minute_C=2.0,
                        mocked_max_orbit_base_temp_C=60.0,
                    ),
                    HeatInfo(
                        max_temp_C=75.0,
                        recommended_high_temp_C=65.0,
                        temperature_C=35.0,
                        radiated_heat_per_minute_C=0.1,
                        temp_inc_per_cpu_minute_C=0.5,
                        mocked_max_orbit_base_temp_C=45.0,
                    ),
                ]
            ),
            edge_nodes=self.generate_edge_nodes(
                satellites_count,
                [
                    {
                        ResourceType.MEMORY_MIB: 2048,
                        ResourceType.MILLI_CPU: 2000,
                    },
                    {
                        ResourceType.MEMORY_MIB: 4096,
                        ResourceType.MILLI_CPU: 4000,
                    }
                ],
                edge_node_locs,
            ),
            cloud_nodes=[],
            ground_stations=self.generate_ground_stations(
                satellites_count + len(edge_node_locs),
                [
                    {
                        ResourceType.MEMORY_MIB: 32768,
                        ResourceType.MILLI_CPU: 32000,
                    }
                ],
                ground_station_locs,
            )
        )

    def generate_random_locations(self, count: int, bounds: tuple[tuple[float, float], tuple[float, float]]) -> list[tuple[float, float]]:
        lat_min = min(bounds[0][0], bounds[1][0])
        lat_max = max(bounds[0][0], bounds[1][0])
        long_min = min(bounds[0][1], bounds[1][1])
        long_max = max(bounds[0][1], bounds[1][1])

        locs: list[tuple[float, float]] = [
            (self.__random.uniform(lat_min, lat_max), self.__random.uniform(long_min, long_max)) for i in range(1, count)
        ]
        return locs
