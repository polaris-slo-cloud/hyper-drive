
from scheduler.model.node import AvailableNodesIndexed, Node

class NodesManager:
    '''Maintains a directory of all nodes.'''

    def __init__(self, all_nodes: AvailableNodesIndexed):
        self.all_nodes = all_nodes

    def get_node_by_name(self, name: str) -> Node | None:
        '''Gets a node using its name.'''
        node = self.all_nodes.satellites.get(name)
        if node:
            return node

        node = self.all_nodes.ground_stations.get(name)
        if node:
            return node

        node = self.all_nodes.edge_nodes.get(name)
        if node:
            return node

        return self.all_nodes.cloud_nodes.get(name)
