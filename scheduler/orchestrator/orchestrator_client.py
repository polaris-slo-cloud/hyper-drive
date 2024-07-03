from abc import ABC, abstractmethod
from scheduler.model import Node, Task

class OrchestratorClient(ABC):
    '''Provides access to the underlying orchestrator.'''

    @abstractmethod
    def get_node_by_name(self, name: str) -> Node | None:
        '''Gets a node using its name.'''
        pass

    @abstractmethod
    def get_latency(self, src: Node, dest: Node) -> float:
        '''
        Gets the current latency in ms between the src node and the dest node.
        If there is no path between src and dest, -1 is returned.
        '''
        pass

    @abstractmethod
    def assign_task(self, task: Task, target_node: Node) -> bool:
        '''Assigns the task to the target node if enough resources are available.'''
        pass

