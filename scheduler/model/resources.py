from enum import Enum

class ResourceType(Enum):
    MILLI_CPU = 'milliCpu'
    MEMORY_MIB = 'memoryMiB'

    BATTERY_MAH = 'batteryMAh'
    '''The remaining battery charge in mAh.'''

    RECHARGE_CAPACITY_WATTS = 'rechargeCapWatts'
    '''The recharge capacity of the satellite's solar panels.'''


class CpuArchitecture(Enum):
    INTEL64 = 'x86_64'
    ARM64 = 'arm64'
