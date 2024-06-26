from scheduler.model import Node, Task
from scheduler.pipeline import FilterPlugin, SchedulingContext


class ResourcesFitPlugin(FilterPlugin):

    def filter(self, node: Node, task: Task, ctx: SchedulingContext) -> bool:
        if task.cpu_architectures and task.cpu_architectures.count(node.cpu_arch) == 0:
            return False

        for key, req_qty in task.req_resources.items():
            available_qty = node.resources.get(key, None)
            if available_qty is None or available_qty < req_qty:
                return False
        return True
