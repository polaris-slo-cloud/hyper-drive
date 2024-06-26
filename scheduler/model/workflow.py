from dataclasses import dataclass
from typing import Generator, Sequence, cast
import networkx as nx
from .node import Node
from .slos import DataSourceSLO, NetworkSLO
from .task import Task

@dataclass
class PredecessorConfig:
    predecessor: Task
    slo: NetworkSLO | None


class Workflow:
    '''
    Represents an entire workflow to be scheduled.
    '''

    def __init__(self):
        self.dag = nx.DiGraph()
        '''The nodes of the DAG are Task objects'''

        self.__start: Task | None = None
        '''The first task of the workflow.'''

        self.scheduled_tasks: dict[Task, Node | None] = {}
        '''
        Maps already scheduled tasks to their target nodes.
        Tasks that have not been assigned yet are not present in the dictionary.
        If no eligible node can be found for a task, None is set as the value.
        '''


    @property
    def start(self) -> Task | None:
        '''The first task of the workflow.'''
        return self.__start


    def add_task(
            self,
            task: Task,
            predecessors: Sequence[PredecessorConfig] | None = None,
        ):
        '''
        Adds the task and connects it to the specified predecessor tasks.
        For each predecessor, a network SLO for the connection from the predecessor to this task can be defined.
        '''

        if predecessors is not None:
            for pred_conf in predecessors:
                if not self.dag.has_node(pred_conf.predecessor):
                    raise ValueError(f'Predecessor task {pred_conf.predecessor.name} does not exist in workflow.')

        self.dag.add_node(task)
        if self.__start is None:
            self.__start = task

        if predecessors is not None:
            for pred_conf in predecessors:
                self.dag.add_edge(pred_conf.predecessor, task, __NETWORK_SLO=pred_conf.slo)


    def get_link_slo(self, task_u: Task, task_v: Task) -> NetworkSLO | None:
        '''Gets the network SLO between task_u and task_v.'''
        edge_data = self.dag.get_edge_data(task_u, task_v)
        if edge_data is None:
            raise ValueError(f'The link ({task_u.name}, {task_v.name}) does not exist.')
        return cast(NetworkSLO, edge_data['__NETWORK_SLO'])


    def get_successors(self, task: Task) -> list[Task]:
        '''Gets the successors of the specified task. Returns an empty list if this was the last task.'''
        successors_it = self.dag.successors(task)
        successors: list[Task] = [ cast(Task, t) for t in successors_it ]
        return successors


    def incoming_link_slos(self, task: Task) -> Generator[tuple[NetworkSLO, Task, Node | None], None, None]:
        '''
        Allows iterating over all incoming task link network SLOs for the specified task.

        On each iteration, the return value is (NetworkSLO, Task, Node | None).
        1. The SLO.
        2. The predecessor task.
        3. The node on which the respective predecessor Task has been scheduled or None if it has not been scheduled yet.
        '''

        for pred in self.dag.predecessors(task):
            slo = self.get_link_slo(pred, task)
            if slo is not None:
                yield slo, pred, self.scheduled_tasks.get(pred)


    def all_incoming_slos(self, task: Task) -> Generator[tuple[NetworkSLO, Node], None, None]:
        '''
        Allows iterating over all incoming network SLOs for the specified task, including DataSourceSLOs.

        On each iteration, the return value is (NetworkSLO, Node).
        1. The SLO.
        2. The node on which the respective predecessor Task has been scheduled or the node of the data source.

        If a predecessor task has not been scheduled yet, an error is raised.
        '''
        for slo, predecessor, node in self.incoming_link_slos(task):
            if node is None:
                raise ValueError(f'Predecessor task {predecessor.name} has not been scheduled yet.')
            yield slo, node

        for slo in task.data_source_slos:
            yield slo, slo.data_source
