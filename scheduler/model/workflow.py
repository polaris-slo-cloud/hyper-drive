import networkx as nx
from scheduler.model.node import CpuArchitecture


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
        

    def add_task(self, task: Task, predecessor: Task = None):
        if predecessor is not None:
            if not self.dag.has_node(predecessor):
                raise ValueError(f'Predecessor task {predecessor.name} does not exist in workflow.')
        
        self.dag.add_node(task)
        if predecessor is not None:
            self.dag.add_edge(predecessor, task)
    