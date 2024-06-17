from scheduler.model import Node

def index_nodes[T: Node](nodes: list[T]) -> dict[str, T]:
    ret: dict[str, T] = {}
    for node in nodes:
        ret[node.name] = node
    return ret
