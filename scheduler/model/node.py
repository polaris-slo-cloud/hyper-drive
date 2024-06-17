from dataclasses import dataclass
from enum import Enum
import uuid

MILLI_CPU = 'milliCpu'
MEMORY_MIB = 'memoryMiB'

BATTERY_MAH = 'batteryMAh'
'''The remaining battery charge in mAh.'''

RECHARGE_CAPACITY_WATTS = 'rechargeCapWatts'
'''The recharge capacity of the satellite's solar panels.'''

class CpuArchitecture(Enum):
    INTEL64 = 'x86_64'
    ARM64 = 'arm64'

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

    def __init__(self, name: str, resources: dict[str, int], cpu_arch: CpuArchitecture):
        if name is None:
            name = uuid.uuid4()
        if cpu_arch is None:
            raise ValueError('cpu_arch must not be None')
        
        if resources is None:
            resources = {}
        self.resources = resources
        '''All resources of this node.'''

        if cpu_arch is None:
            cpu_arch = CpuArchitecture.INTEL64
        self.cpu_arch = cpu_arch

    @property
    def milli_cpu(self) -> int:
        return self.resources[MILLI_CPU]
    
    @milli_cpu.setter
    def set_milli_cpu(self, mcpu: int):
        self.resources[MILLI_CPU] = mcpu

    @property
    def memory_mib(self) -> int:
        return self.resources[MEMORY_MIB]
    
    @memory_mib.setter
    def set_memory_mib(self, memory_mib: int):
        self.resources[MEMORY_MIB] = memory_mib



class TerrestrialNode(Node):
    '''
    A Node located on Earth.
    '''

    def __init__(self, name: str, resources: dict[str, int], loc: Location = None):
        super().__init__(name=name, resources=resources)
        self.location = loc


class GroundStationNode(TerrestrialNode):
    pass


class EdgeNode(TerrestrialNode):
    pass


class SatelliteNode(Node):
    
    def __init__(self, name: str, resources: dict[str, int]):
        super().__init__(name=name, resources=resources)