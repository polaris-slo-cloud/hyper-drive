from scheduler.model import EligibleNode, Node, Task
from scheduler.pipeline import SchedulingContext, ScorePlugin

class FirstFitPlugin(ScorePlugin):
    '''Score plugin for simulating a greedy first fit scheduler'''

    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        return 0


    def normalize_scores(self, task: Task, node_scores: list[EligibleNode], ctx: SchedulingContext):
        node_scores[0].score = 100
