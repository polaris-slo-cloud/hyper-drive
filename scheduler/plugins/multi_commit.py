from scheduler.model import EligibleNode, Task
from scheduler.pipeline import CommitPlugin, SchedulingContext

NODES_TO_TRY = 3

class MultiCommitPlugin(CommitPlugin):

    def commit(self, task: Task, scored_nodes: list[EligibleNode], ctx: SchedulingContext) -> EligibleNode | None:
        nodes_tried = 0
        for node in scored_nodes:
            if nodes_tried == NODES_TO_TRY:
                break
            if ctx.orchestrator.assign_task(task, node.node):
                return node
            nodes_tried += 1
        return None
