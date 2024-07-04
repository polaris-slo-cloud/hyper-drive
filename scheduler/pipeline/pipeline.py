from abc import ABC, abstractmethod
from dataclasses import dataclass
from scheduler.model import AvailableNodes, Node, EligibleNode, Task, Workflow
from scheduler.orchestrator import OrchestratorClient

@dataclass
class SchedulingContext:
    workflow: Workflow
    orchestrator: OrchestratorClient


class SelectCandidateNodesPlugin(ABC):
    '''
    Plugin for assembling a list of candidate nodes that are then passed to the filter plugins.
    SelectCandidateNodes plugins can, e.g., be used to pre-select only nodes in the vicinity of the source.
    '''

    def select_candidates(self, task: Task, all_nodes: AvailableNodes, ctx: SchedulingContext) -> dict[str, Node] | None:
        '''
        Selects a list of candidate nodes that will be passed to the filter plugins.
        If no nodes are eligible as candidates, an empty dictionary is returned.
        If the all nodes are eligible as candidates, None is returned.
        '''
        pass


class FilterPlugin(ABC):
    '''Plugin to filter out non-eligible nodes for hosting a task.'''

    @abstractmethod
    def filter(self, node: Node, task: Task, ctx: SchedulingContext) -> bool:
        '''
        Returns true if the node can host the task, otherwise false.
        '''
        pass


class ScorePlugin(ABC):
    '''
    Plugin to determine how well suited an eligible node is for a task by assigning a score.

    The final score for every node will be in the range [0, 100]. However, if normalize_scores()
    is implemented, score() may return other numbers as well.
    '''

    @abstractmethod
    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        '''
        Returns a score for the specified node.
        The final score is in the range [0, 100]. However, if normalize_scores()
        is implemented, score() may return other numbers as well.
        '''
        pass


    def normalize_scores(self, task: Task, node_scores: list[EligibleNode], ctx: SchedulingContext):
        '''Optional method that normalizes the node scores (in place) to the range [0, 100].'''
        pass


class CommitPlugin(ABC):
    '''
    Plugin to assign the task to the most suitable node in the orchestrator.
    '''

    @abstractmethod
    def commit(self, task: Task, scored_nodes: list[EligibleNode], ctx: SchedulingContext) -> EligibleNode | None:
        '''
        Assigns the task to the most suitable node in the orchestrator. If this is not possible, another node
        may be selected from the list of scored_nodes, which is sorted from highest to lowest score.

        Returns the node to which the task was assigned or None, if not assignment was possible.
        '''
        pass
