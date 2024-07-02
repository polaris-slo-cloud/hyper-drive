
from dataclasses import dataclass
from scheduler.model import AvailableNodes, AvailableNodesIndexed, Node, EligibleNode, Task, Workflow
from scheduler.orchestrator import OrchestratorClient
from scheduler.pipeline import CommitPlugin, FilterPlugin, SchedulingContext, ScorePlugin, SelectCandidateNodesPlugin
from scheduler.util import Timer, index_nodes

@dataclass
class SchedulingResult:
    success: bool
    task: str
    scheduling_duration_msec: int
    failure_reason: str | None = None
    target_node_type: str | None = None
    target_node: str | None = None
    score: int | None = None


@dataclass
class SchedulerConfig:
    select_candidate_nodes_plugin: SelectCandidateNodesPlugin
    filter_plugins: list[FilterPlugin]
    score_plugins: list[ScorePlugin]
    commit_plugin: CommitPlugin
    orchestrator_client: OrchestratorClient


class Scheduler:

    def __init__(self, config: SchedulerConfig, nodes: AvailableNodes):
        self.__select_candidate_nodes_plugin = config.select_candidate_nodes_plugin
        self.__filter_plugins = config.filter_plugins
        self.__score_plugins = config.score_plugins
        self.__commit_plugin = config.commit_plugin
        self.__orchestrator = config.orchestrator_client

        self.__avail_nodes = AvailableNodesIndexed(
            cloud_nodes=index_nodes(nodes.cloud_nodes),
            ground_stations=index_nodes(nodes.ground_stations),
            edge_nodes=index_nodes(nodes.edge_nodes),
            satellites=index_nodes(nodes.satellites),
        )


    def schedule(self, task: Task, workflow: Workflow) -> SchedulingResult:
        '''
        Schedules the specified task of the workflow on the most suitable node.
        '''
        timer = Timer()
        timer.start()
        ctx = SchedulingContext(workflow=workflow, orchestrator=self.__orchestrator)

        def scheduling_failure(reason: str) -> SchedulingResult:
            timer.stop()
            workflow.scheduled_tasks[task] = None
            return SchedulingResult(success=False, task=task.name, scheduling_duration_msec=timer.duration_ms(), failure_reason=reason)

        candidate_nodes = self.__select_candidate_nodes_plugin.select_candidates(task, self.__avail_nodes, ctx)
        if candidate_nodes is not None:
            if len(candidate_nodes) == 0:
                return scheduling_failure('No candidate nodes')
            eligible_nodes = self.__filter_nodes(task, ctx, candidate_nodes, [])
        else:
            eligible_nodes = self.__filter_default_nodes(task, ctx)

        if len(eligible_nodes) == 0:
            return scheduling_failure('Filtering returned no eligible nodes')

        self.__score_nodes(task, ctx, eligible_nodes)

        target_node = self.__commit_task(task, eligible_nodes, workflow, ctx)
        if target_node is None:
            return scheduling_failure(f'Could not commit task {task.name} due to scheduling conflicts.')

        timer.stop()
        return SchedulingResult(
            success=True,
            task=task.name,
            target_node=target_node.node.name,
            target_node_type=type(target_node).__name__,
            score=target_node.score,
            scheduling_duration_msec=timer.duration_ms(),
        )


    def force_schedule(self, task: Task, workflow: Workflow, target_node: Node) -> SchedulingResult:
        '''
        Assigns the specified task to the target_node. This can be used to set up a starting point for an experiment,
        where a part of the workflow is already executing.
        '''
        ctx = SchedulingContext(workflow=workflow, orchestrator=self.__orchestrator)
        target = [ EligibleNode(node=target_node, score=100) ]
        if self.__commit_task(task, target, workflow, ctx) is None:
            raise SystemError(f'Could not force schedule task {task.name} to node {target_node.name}.')

        return SchedulingResult(
            success=True,
            task=task.name,
            target_node=target_node.name,
            target_node_type=type(target_node).__name__,
            score=100,
            scheduling_duration_msec=0,
        )


    def __filter_default_nodes[T: Node](self, task: Task, ctx: SchedulingContext) -> list[EligibleNode]:
        eligible_nodes: list[EligibleNode] = []
        self.__filter_nodes(task, ctx, self.__avail_nodes.cloud_nodes, eligible_nodes)
        self.__filter_nodes(task, ctx, self.__avail_nodes.ground_stations, eligible_nodes)
        self.__filter_nodes(task, ctx, self.__avail_nodes.edge_nodes, eligible_nodes)
        self.__filter_nodes(task, ctx, self.__avail_nodes.satellites, eligible_nodes)
        return eligible_nodes


    def __filter_nodes[T: Node](self, task: Task, ctx: SchedulingContext, nodes: dict[str, T], eligible_nodes: list[EligibleNode]) -> list[EligibleNode]:
        for node in nodes.values():
            eligible = True
            for filter in self.__filter_plugins:
                if not filter.filter(node, task, ctx):
                    eligible = False
                    break

            if eligible:
                eligible_nodes.append(EligibleNode(node, 0))

        return eligible_nodes


    def __score_nodes(self, task: Task, ctx: SchedulingContext, eligible_nodes: list[EligibleNode]):
        for score_plugin in self.__score_plugins:
            self.__run_score_plugin(score_plugin, task, ctx, eligible_nodes)

        for node in eligible_nodes:
            node.score = int(node.score / len(self.__score_plugins))

        eligible_nodes.sort(reverse=True, key=lambda n: n.score)


    def __run_score_plugin(self, score_plugin: ScorePlugin, task: Task, ctx: SchedulingContext, eligible_nodes: list[EligibleNode]):
        '''Runs the score plugin and adds its score to each node.'''
        node_scores: list[EligibleNode] = []
        for node in eligible_nodes:
            score = score_plugin.score(node.node, task, ctx)
            node_scores.append(EligibleNode(node.node, score))

        score_plugin.normalize_scores(task, node_scores, ctx)
        for i, node in enumerate(eligible_nodes):
            node.score += node_scores[i].score


    def __commit_task(self, task: Task, scored_nodes: list[EligibleNode], workflow: Workflow | None, ctx: SchedulingContext) -> EligibleNode | None:
        committed_node = self.__commit_plugin.commit(task, scored_nodes, ctx)
        if committed_node is None:
            return None

        if workflow is not None:
            workflow.scheduled_tasks[task] = committed_node.node
        return committed_node
