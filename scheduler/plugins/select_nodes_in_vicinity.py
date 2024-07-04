from typing import cast
from random import Random
from scheduler.model import AvailableNodes, Location, Node, SatelliteNode, Task, TerrestrialNode
from scheduler.pipeline import SchedulingContext, SelectCandidateNodesPlugin
from scheduler.util import index_nodes_into
from geopy import distance

class SelectNodesInVicinityPlugin(SelectCandidateNodesPlugin):
    '''
    Selects nodes in the vicinity of the first predecessor node.

    IMPORTANT: If the task to be scheduled is the first task of a workflow, random nodes are picked, because there is no predecessor,
    because at the moment our model does not allow a task to specify a desired location.
    '''

    def __init__(
        self,
        radius_ground_km: float,
        radius_edge_km: float,
        radius_space_km: float,
        ground_nodes_count: int,
        edge_nodes_count: int,
        space_nodes_count: int,
    ):
        self.__radius_ground_km = radius_ground_km
        self.__radius_edge_km = radius_edge_km
        self.__radius_space_km = radius_space_km
        self.__ground_nodes_count = ground_nodes_count
        self.__edge_nodes_count = edge_nodes_count
        self.__space_nodes_count = space_nodes_count
        self.__random = Random(radius_ground_km)


    def select_candidates(self, task: Task, all_nodes: AvailableNodes, ctx: SchedulingContext) -> dict[str, Node] | None:
        location = self.__get_desired_location(task, ctx)
        if not location:
            return self.__pick_random_nodes(all_nodes)

        selection: dict[str, Node] = {}
        added = self.__add_nodes(
            src_loc=location,
            candidates=all_nodes.ground_stations,
            selection=selection,
            max_distance_km=self.__radius_ground_km,
            count=self.__ground_nodes_count,
            ctx=ctx,
        )
        if added < self.__ground_nodes_count:
            missing = self.__ground_nodes_count - added
            self.__add_nodes(
                src_loc=location,
                candidates=all_nodes.cloud_nodes,
                selection=selection,
                max_distance_km=self.__radius_ground_km,
                count=missing,
                ctx=ctx,
            )
        self.__add_nodes(
            src_loc=location,
            candidates=all_nodes.edge_nodes,
            selection=selection,
            max_distance_km=self.__radius_edge_km,
            count=self.__edge_nodes_count,
            ctx=ctx,
        )
        self.__add_nodes(
            src_loc=location,
            candidates=all_nodes.satellites,
            selection=selection,
            max_distance_km=self.__radius_space_km,
            count=self.__space_nodes_count,
            ctx=ctx,
        )
        return selection


    def __get_desired_location(self, task: Task, ctx: SchedulingContext) -> Location | None:
        pred_tasks = ctx.workflow.get_predecessors(task)
        if len(pred_tasks) == 0:
            return None
        pred_node = ctx.workflow.scheduled_tasks.get(pred_tasks[0])
        if not pred_node:
            raise SystemError(f'Predecessor task {pred_tasks[0].name} has not been scheduled.')

        if isinstance(pred_node, TerrestrialNode):
            return pred_node.location
        if isinstance(pred_node, SatelliteNode):
            satellite_loc = ctx.orchestrator.get_satellite_position(pred_node)
            return Location(lat=satellite_loc[0], long=satellite_loc[1], altitude_km=satellite_loc[2])
        raise SystemError(f'Unknown predecessor node type: {type(pred_node)}')


    def __get_node_location_lat_long(self, node: Node, ctx: SchedulingContext) -> tuple[float, float]:
        if isinstance(node, TerrestrialNode):
            return (node.location.lat, node.location.long)
        if isinstance(node, SatelliteNode):
            satellite_loc = ctx.orchestrator.get_satellite_position(node)
            return (satellite_loc[0], satellite_loc[1])
        raise SystemError(f'Cannot get location of unknown node type: {type(node)}')


    def __add_nodes[T: Node](
        self,
        src_loc: Location,
        candidates: list[T],
        selection: dict[str, Node],
        max_distance_km: float,
        count: int,
        ctx: SchedulingContext,
    ) -> int:
        src = (src_loc.lat, src_loc.long)
        added = 0

        for candidate in candidates:
            if added == count:
                break
            candidate_loc = self.__get_node_location_lat_long(candidate, ctx)
            dist = distance.geodesic(src, candidate_loc)
            if dist.km <= max_distance_km:
                selection[candidate.name] = candidate
                added += 1
        return added


    def __pick_random_nodes(self, all_nodes: AvailableNodes) -> dict[str, Node]:
        selection: dict[str, Node] = {}
        added = self.__add_random_nodes(all_nodes.ground_stations, selection, self.__ground_nodes_count)
        if added < self.__ground_nodes_count:
            missing = self.__ground_nodes_count - added
            self.__add_random_nodes(all_nodes.cloud_nodes, selection, missing)
        self.__add_random_nodes(all_nodes.edge_nodes, selection, self.__edge_nodes_count)
        self.__add_random_nodes(all_nodes.satellites, selection, self.__space_nodes_count)
        return selection


    def __add_random_nodes[T: Node](self, candidates: list[T], selection: dict[str, Node], count: int) -> int:
        count = min(count, len(candidates))
        if count == 0:
            return 0
        picked_nodes = self.__random.choices(population=candidates, k=count)
        index_nodes_into(cast(list[Node], picked_nodes), selection)
        return count
