import math
from scheduler.model import Node, NodeScore, Task
from scheduler.pipeline import FilterPlugin, SchedulingContext, ScorePlugin

class NetworkQosPlugin(FilterPlugin, ScorePlugin):

    def filter(self, node: Node, task: Task, ctx: SchedulingContext) -> bool:
        for slo, src_node in ctx.workflow.all_incoming_slos(task):
            if slo.max_latency_msec is not None:
                latency = round(ctx.orchestrator.get_latency(src_node, node), 0)
                if latency > slo.max_latency_msec:
                    return False
        return True


    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        highest_latency = 0.0
        for slo, src_node in ctx.workflow.all_incoming_slos(task):
            latency = ctx.orchestrator.get_latency(src_node, node)
            highest_latency = max(highest_latency, latency)
        return int(round(highest_latency, 0))


    def normalize_scores(self, task: Task, node_scores: list[NodeScore], ctx: SchedulingContext):
        '''
        Normalizes the scores to the range [0; 100] using the following procedure:
        1. Compute max_diff = the difference between the lowest and the highest latency
        2. For each score compute its diff to the highest latency as a percentage of max_diff and set the score to that.
        '''
        lowest_latency = 1000000000
        highest_latency = 0
        for node_score in node_scores:
            if node_score.score > highest_latency:
                highest_latency = node_score.score
            if node_score.score < lowest_latency:
                lowest_latency = node_score.score

        max_diff = float(highest_latency - lowest_latency)
        if max_diff == 0.0:
            max_diff = 1.0

        for node_score in node_scores:
            diff = highest_latency - node_score.score
            percentage = float(diff) / max_diff
            score = math.floor(percentage * 100)
            node_score.score = score
