from scheduler.model import EligibleNode, Node, Task
from scheduler.pipeline import SchedulingContext, ScorePlugin

class RoundRobinPlugin(ScorePlugin):
    '''Score plugin for simulating a Round Robin scheduler'''

    def __init__(self, total_nodes: int):
        self.__last_node_id = -1
        self.__total_nodes = total_nodes


    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        return 0


    def normalize_scores(self, task: Task, node_scores: list[EligibleNode], ctx: SchedulingContext):
        next_id = self.__last_node_id + 1
        if next_id == self.__total_nodes:
            next_id = 0

        lowest_id_greater_equal_next = self.__total_nodes
        lowest_node_greater_equal_next: EligibleNode | None = None
        lowest_id = self.__total_nodes
        lowest_id_node: EligibleNode | None = None
        for scored_node in node_scores:
            node_id = int(scored_node.node.name)
            if node_id >= next_id and node_id < lowest_id_greater_equal_next:
                lowest_id_greater_equal_next = node_id
                lowest_node_greater_equal_next = scored_node
            if node_id < lowest_id:
                lowest_id = node_id
                lowest_id_node = scored_node

        # Check if we have found a node >= next_id.
        if lowest_node_greater_equal_next:
            lowest_node_greater_equal_next.score = 100
            self.__last_node_id = lowest_id_greater_equal_next
            return

        # We need to wrap the ID counter around to 0 (actually to the lowest ID that we could find).
        if not lowest_id_node:
            raise SystemError('The list of node_scores was empty.')
        lowest_id_node.score = 100
        self.__last_node_id = lowest_id


