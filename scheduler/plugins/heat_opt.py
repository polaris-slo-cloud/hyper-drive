import math
from scheduler.model import Node, SatelliteNode, Task
from scheduler.pipeline import SchedulingContext, ScorePlugin
from scheduler.util import HeatEstimator

class HeatOptPlugin(ScorePlugin):
    '''
    Score plugin to favor satellites that will not overheat with the new task.
    For terrestrial nodes this plugin always returns the top score.
    '''

    def __init__(self):
        self.__heat_estimator = HeatEstimator()

    def score(self, node: Node, task: Task, ctx: SchedulingContext) -> int:
        if not isinstance(node, SatelliteNode):
            return 100

        expected_max_temp = self.__heat_estimator.estimate_max_temp(node, task)
        return self.__compute_score(
            expected_temp=expected_max_temp,
            recommended_temp=node.heat_status.recommended_high_temp_C,
            max_temp=node.heat_status.max_temp_C,
        )


    def __compute_score(self, expected_temp: float, recommended_temp: float, max_temp: float) -> int:
        if expected_temp <= recommended_temp:
            return 100
        if expected_temp > max_temp:
            return 0

        range = max_temp - recommended_temp # range cannot be 0, because otherwise expected_temp <= recommended_temp would be true
        over_recommended = expected_temp - recommended_temp
        inv_percentage_over = 1 - over_recommended / range
        return int(math.floor(inv_percentage_over * 100))
