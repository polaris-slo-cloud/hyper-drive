from typing import Optional, cast
import networkx as nx
from scheduler.model.node import CpuArchitecture, Node
from scheduler.model.slos import NetworkSLOs

__NETWORK_SLOS = 'network_slos'

class Task:
    '''
    Represents a single task to be scheduled.
    '''

    def __init__(self, name: str, image: str, req_resources: dict[str, int], cpu_arch: CpuArchitecture):
        if name is None or name == '':
            raise ValueError('name cannot be empty')
        self.name = name
        self.image = image
        if req_resources is None or len(req_resources) == 0:
            raise ValueError('req_resources must not be empty')
        self.req_resources = req_resources
        self.cpu_arch = cpu_arch


    def __hash__(self) -> int:
        return self.name.__hash__();


class Workflow:
    '''
    Represents an entire workflow to be scheduled.
    '''

    def __init__(self):
        self.dag = nx.DiGraph()
        '''The nodes of the DAG are Task objects'''

        self.scheduled_tasks: dict[Task, Node | None] = {}
        '''
        Maps already scheduled tasks to their target nodes.
        Tasks that have not been assigned yet are not present in the dictionary.
        If no eligible node can be found for a task, None is set as the value.
        '''


    def add_task(self, task: Task, predecessor: Optional[Task] = None, network_slos: Optional[NetworkSLOs] = None):
        if predecessor is not None:
            if not self.dag.has_node(predecessor):
                raise ValueError(f'Predecessor task {predecessor.name} does not exist in workflow.')
        else:
            if network_slos is not None:
                raise ValueError('SLOs require a predecessor node')

        self.dag.add_node(task)
        if predecessor is not None:
            self.dag.add_edge(predecessor, task, __NETWORK_SLOS=network_slos)


    def get_edge_slos(self, task_u: Task, task_v: Task) -> NetworkSLOs | None:
        '''Gets the network SLOs between task_u and task_v.'''
        edge_data = self.dag.get_edge_data(task_u, task_v)
        if edge_data is None:
            raise ValueError(f'The edge ({task_u.name}, {task_v.name}) does not exist.')
        return cast(NetworkSLOs, edge_data[__NETWORK_SLOS])
