from dataclasses import dataclass

@dataclass
class NetworkSLOs:
    '''Defines network SLOs for the connection between two tasks.'''

    min_bandwidth_kpbs: int | None
    max_latency_msec: int | None
