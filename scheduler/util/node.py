from scheduler.model import Node

def index_nodes[T: Node](nodes: list[T]) -> dict[str, T]:
    ret: dict[str, T] = {}
    index_nodes_into(nodes, ret)
    return ret


def index_nodes_into[T: Node](nodes: list[T], dest: dict[str, T]):
    for node in nodes:
        dest[node.name] = node
