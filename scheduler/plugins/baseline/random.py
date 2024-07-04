from random import Random
from scheduler.model import EligibleNode, Node, Task
from scheduler.pipeline import SchedulingContext, ScorePlugin

class RandomSelectionPlugin(ScorePlugin):
    '''Score plugin for simulating a random scheduler'''

    def __init__(self):
        self.__random = Random()

    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        return 0


    def normalize_scores(self, task: Task, node_scores: list[EligibleNode], ctx: SchedulingContext):
        index = self.__random.randint(0, len(node_scores) - 1)
        node_scores[index].score = 100
