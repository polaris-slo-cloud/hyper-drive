from typing import Optional
from scheduler.model.node import Node
from scheduler.model.workflow import Task, Workflow


class FilterPlugin:
    '''Plugin to filter out non-eligible nodes for hosting a task.'''

    def filter(node: Node, task: Task, workflow: Optional[Workflow]) -> bool:
        '''
        Returns true if the node can host the task, otherwise false.
        '''
        pass


class ScorePlugin:
    '''Plugin to determine how well suited an eligible node is for a task by assigning a score.'''

    def score(node: Node, task: Task, workflow: Optional[Workflow]) -> int:
        '''Returns a score in the range [0, 100].'''
        pass