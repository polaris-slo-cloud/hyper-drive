from dataclasses import dataclass
from typing import Optional
import uuid
from .resources import CpuArchitecture, ResourceType

@dataclass
class Location:
    '''Describes a location on Earth or in the air.'''

    lat: float
    long: float
    altitude_km: float
    '''The altitude of the node in kilometers. This is 0 for ground-based nodes.'''

@dataclass
class LocationAndDistance(Location):
    max_distance_km: float


@dataclass
class HeatInfo:
    temperature_C: float
    '''The current temperature of the satellite in deg Celsius.'''

    max_temp_C: float
    '''
    The maximum operating temperature in deg Celsius.
    Above this temperature the satellite needs to reduce computing capacity to avoid damage.
    '''

    recommended_high_temp_C: float
    '''The recommended highest temperature of the satellite. This is less than `max_temp_C` and is just a recommendation that can be safely exceeded.'''

    temp_inc_per_cpu_minute_C: float
    '''The amount of temperature increase expected by full load on one CPU core per minute.'''

    radiated_heat_per_minute_C: float
    '''
    The amount of temperature decrease per minute due to radiator cooling panels.
    This is a positive number that can be subtracted from the increase.
    '''

    mocked_max_orbit_base_temp_C: float
    '''
    The mocked max temperature that the satellite will experience in its orbit during the runtime of the task.
    Compute the max orbit temp using this formula:
    `mocked_max_orbit_base_temp_C` * `expected_runtime_minutes` mod `int(max_temp_C)`
    '''


class Node:
    '''
    Describes a general purpose compute node.
    '''

    def __init__(self, name: str, resources: dict[ResourceType, int], cpu_arch: CpuArchitecture):
        if name is None:
            name = str(uuid.uuid4())
        self.name = name
        if cpu_arch is None:
            raise ValueError('cpu_arch must not be None')
        self.cpu_arch = cpu_arch

        if resources is None:
            resources = {}
        self.resources = resources
        '''
        All available resources of this node.

        See the ResourceType enum for a list of available resource types.
        '''

        self.capacity = resources.copy()
        '''The total resource capacity of the node (free + used).'''

    @property
    def milli_cpu(self) -> int:
        return self.resources[ResourceType.MILLI_CPU]

    @milli_cpu.setter
    def set_milli_cpu(self, mcpu: int):
        self.resources[ResourceType.MILLI_CPU] = mcpu

    @property
    def memory_mib(self) -> int:
        return self.resources[ResourceType.MEMORY_MIB]

    @memory_mib.setter
    def set_memory_mib(self, memory_mib: int):
        self.resources[ResourceType.MEMORY_MIB] = memory_mib



class TerrestrialNode(Node):
    '''
    A Node located on Earth.
    '''

    def __init__(self, name: str, resources: dict[ResourceType, int], cpu_arch: CpuArchitecture, loc: Location):
        super().__init__(name=name, resources=resources, cpu_arch=cpu_arch)
        self.location = loc


class CloudNode(TerrestrialNode):
    pass


class GroundStationNode(TerrestrialNode):
    pass


class EdgeNode(TerrestrialNode):
    pass


class SatelliteNode(Node):

    def __init__(self, name: str, resources: dict[ResourceType, int], cpu_arch: CpuArchitecture, heat_status: HeatInfo):
        super().__init__(name=name, resources=resources, cpu_arch=cpu_arch)
        self.heat_status = heat_status


@dataclass
class AvailableNodes:
    cloud_nodes: list[CloudNode]
    ground_stations: list[GroundStationNode]
    edge_nodes: list[EdgeNode]
    satellites: list[SatelliteNode]


@dataclass
class AvailableNodesIndexed:
    cloud_nodes: dict[str, CloudNode]
    ground_stations: dict[str, GroundStationNode]
    edge_nodes: dict[str, EdgeNode]
    satellites: dict[str, SatelliteNode]


@dataclass
class EligibleNode:
    '''A node that has passed the Filter stage and that is eligible for hosting the task.'''
    node: Node
    score: int
