from scheduler.model import Node, Task
from scheduler.orchestrator import NodesManager, OrchestratorClient
from scheduler.orchestrator.starrynet.starrynet_time_svc import StarryNetTimeService
from starrynet.starrynet.sn_synchronizer import StarryNet

class StarryNetClient(OrchestratorClient):

    def __init__(self, nodes_mgr: NodesManager, sn: StarryNet, time_svc: StarryNetTimeService):
        self.__nodes_mgr = nodes_mgr
        self.__sn = sn
        self.__time_svc = time_svc

    def get_node_by_name(self, name: str) -> Node | None:
        return self.__nodes_mgr.get_node_by_name(name)

    def get_latency(self, src: Node, dest: Node) -> float:
        return self.__sn.get_delay(int(src.name), int(dest.name), self.__time_svc.curr_time)

    def assign_task(self, task: Task, target_node: Node) -> bool:
        return self.__nodes_mgr.assign_task(task, target_node)
