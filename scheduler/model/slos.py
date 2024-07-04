from dataclasses import dataclass
from .node import Node

@dataclass
class NetworkSLO:
    '''Defines a network SLO for an incoming connection to a Task.'''

    min_bandwidth_kpbs: float | None
    max_latency_msec: float | None


@dataclass
class DataSourceSLO(NetworkSLO):
    '''Defines a network SLO for the link between a data source and the current task.'''

    data_source: Node
