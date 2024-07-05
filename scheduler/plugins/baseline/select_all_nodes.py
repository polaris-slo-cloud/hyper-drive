from typing import cast
from random import Random
from scheduler.model import AvailableNodes, Location, Node, SatelliteNode, Task, TerrestrialNode
from scheduler.pipeline import SchedulingContext, SelectCandidateNodesPlugin
from scheduler.util import index_nodes_into

class SelectAllNodesPlugin(SelectCandidateNodesPlugin):

    def select_candidates(self, task: Task, all_nodes: AvailableNodes, ctx: SchedulingContext) -> dict[str, Node] | None:
        ret: dict[str, Node] = {}
        index_nodes_into(cast(list[Node], all_nodes.ground_stations), ret)
        index_nodes_into(cast(list[Node], all_nodes.cloud_nodes), ret)
        index_nodes_into(cast(list[Node], all_nodes.edge_nodes), ret)
        index_nodes_into(cast(list[Node], all_nodes.satellites), ret)
        return ret
