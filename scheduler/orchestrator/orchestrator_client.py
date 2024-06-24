from abc import ABC, abstractmethod
from scheduler.model import Node

class OrchestratorClient(ABC):
    '''Provides access to the underlying orchestrator.'''

    @abstractmethod
    def get_node_by_name(self, name: str) -> Node | None:
        '''Gets a node using its name.'''
        pass

    @abstractmethod
    def get_latency(self, src: Node, dest: Node) -> float:
        '''Gets the current latency in ms between the src node and the dest node.'''
        pass

