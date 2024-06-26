from dataclasses import dataclass
from typing import Optional
import uuid
from .resources import CpuArchitecture, ResourceType

@dataclass
class Location:
    '''Describes a location on Earth or in the air.'''

    lat: float
    long: float
    altitude_m: float
    '''The altitude of the node in meters. This is 0 for ground-based nodes.'''

@dataclass
class LocationAndDistance(Location):
    max_distance_km: float


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

    def __init__(self, name: str, resources: dict[ResourceType, int], cpu_arch: CpuArchitecture, loc: Optional[Location] = None):
        super().__init__(name=name, resources=resources, cpu_arch=cpu_arch)
        self.location = loc


class CloudNode(TerrestrialNode):
    pass


class GroundStationNode(TerrestrialNode):
    pass


class EdgeNode(TerrestrialNode):
    pass


class SatelliteNode(Node):

    def __init__(self, name: str, resources: dict[ResourceType, int], cpu_arch: CpuArchitecture):
        super().__init__(name=name, resources=resources, cpu_arch=cpu_arch)


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
class NodeScore:
    node: Node
    score: int
