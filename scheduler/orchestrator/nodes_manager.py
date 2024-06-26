
from scheduler.model.node import AvailableNodes, AvailableNodesIndexed, Node
from scheduler.util import index_nodes

class NodesManager:
    '''Maintains a directory of all nodes.'''

    def __init__(self, nodes: AvailableNodes):
        self.all_nodes = AvailableNodesIndexed(
            cloud_nodes=index_nodes(nodes.cloud_nodes),
            ground_stations=index_nodes(nodes.ground_stations),
            edge_nodes=index_nodes(nodes.edge_nodes),
            satellites=index_nodes(nodes.satellites),
        )


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
