from typing import cast
from scheduler.model import AvailableNodesIndexed, Node, Task
from scheduler.pipeline import SchedulingContext, SelectCandidateNodesPlugin
from scheduler.util import copy_dict

class SelectNodesInVicinityPlugin(SelectCandidateNodesPlugin):

    def select_candidates(self, task: Task, all_nodes: AvailableNodesIndexed, ctx: SchedulingContext) -> dict[str, Node] | None:
        ret: dict[str, Node] = {}
        copy_dict(cast(dict[str, Node], all_nodes.satellites), ret)
        copy_dict(cast(dict[str, Node], all_nodes.edge_nodes), ret)
        copy_dict(cast(dict[str, Node], all_nodes.ground_stations), ret)
        copy_dict(cast(dict[str, Node], all_nodes.cloud_nodes), ret)
        return ret
