
from scheduler.model import AvailableNodes, AvailableNodesIndexed, Node, Task
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


    def assign_task(self, task: Task, target_node: Node) -> bool:
        '''Assigns the task to the target node if enough resources are available.'''

        # Check if the resources are available.
        for key, req_qty in task.req_resources.items():
            available_qty = target_node.resources.get(key, None)
            if available_qty is None or available_qty < req_qty:
                return False

        # Assign the resources:
        for key, req in task.req_resources.items():
            target_node.resources[key] -= req
        return True
