from typing import cast
import networkx as nx
from scheduler.model import Node, SatelliteNode, Task
from scheduler.orchestrator import NodesManager, OrchestratorClient
from scheduler.orchestrator.starrynet.starrynet_time_svc import StarryNetTimeService
from starrynet.starrynet.sn_synchronizer import StarryNet

class StarryNetClient(OrchestratorClient):

    def __init__(self, nodes_mgr: NodesManager, sn: StarryNet, time_svc: StarryNetTimeService):
        self.__nodes_mgr = nodes_mgr
        self.__sn = sn
        self.__time_svc = time_svc
        self.__network_graph_time: int = -1
        self.__network_graph: nx.Graph = self.__build_network_graph()
        self.__sat_positions_time: int = -1
        self.__sat_positions: list[tuple[float, float, float]] = []


    def get_node_by_name(self, name: str) -> Node | None:
        return self.__nodes_mgr.get_node_by_name(name)


    def get_latency(self, src: Node, dest: Node) -> float:
        graph = self.get_network_graph()
        path: list[int]
        try:
            path = cast(list[int], nx.shortest_path(graph, int(src.name), int(dest.name), 'latency'))
        except nx.NetworkXNoPath as ex:
            return -1

        total_latency = 0.0
        u: int | None = None
        for v in path:
            if u is not None:
                latency = graph.get_edge_data(u, v)['latency']
                total_latency += latency
            u = v
        return total_latency


    def assign_task(self, task: Task, target_node: Node) -> bool:
        return self.__nodes_mgr.assign_task(task, target_node)


    def get_satellite_position(self, node: SatelliteNode) -> tuple[float, float, float]:
        if self.__sat_positions_time != self.__time_svc.curr_time:
            self.__sat_positions = self.__sn.get_positions(self.__time_svc.curr_time)
            self.__sat_positions_time = self.__time_svc.curr_time
        return self.__sat_positions[int(node.name)]


    def get_network_graph(self) -> nx.Graph:
        if self.__network_graph_time != self.__time_svc.curr_time:
            self.__update_network_graph()
        return self.__network_graph


    def __build_network_graph(self) -> nx.Graph:
        all_nodes = self.__nodes_mgr.all_nodes
        nodes_count = len(all_nodes.satellites) + len(all_nodes.edge_nodes) + len(all_nodes.cloud_nodes) + len(all_nodes.ground_stations)
        graph = nx.Graph()
        for i in range(nodes_count):
            graph.add_node(i)
        return graph


    def __update_network_graph(self):
        delays = self.__sn.get_delay_matrix(self.__time_svc.curr_time)
        nodes_count = self.__network_graph.number_of_nodes()

        # We need to clear all edges, because the connections between nodes may change as the simulation progresses.
        self.__network_graph.clear_edges()

        # We iterate through the top diagonal part of the delays_matrix to set the edge weights.
        for i in range(nodes_count):
            for j in range(i + 1, nodes_count):
                latency = delays[i][j]
                if latency != 0.0:
                    self.__network_graph.add_edge(i, j, latency=latency)

        self.__network_graph_time = self.__time_svc.curr_time
