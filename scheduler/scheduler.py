
from dataclasses import dataclass
from scheduler.model import AvailableNodes, AvailableNodesIndexed, Node, EligibleNode, SatelliteNode, Task, Workflow
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
    avg_pred_latency_slo: float | None = None
    avg_pred_latency: float | None = None
    avg_data_latency_slo: float | None = None
    avg_data_latency: float | None = None
    deg_C_over_recommended: float | None = None
    deg_C_over_max: float | None = None


@dataclass
class SchedulerConfig:
    select_candidate_nodes_plugin: SelectCandidateNodesPlugin
    filter_plugins: list[FilterPlugin]
    score_plugins: list[ScorePlugin]
    commit_plugin: CommitPlugin
    orchestrator_client: OrchestratorClient


@dataclass
class _TaskLatencies:
    avg_pred_latency_slo: float | None = None
    avg_pred_latency: float | None = None
    avg_data_latency_slo: float | None = None
    avg_data_latency: float | None = None


@dataclass
class _TemperatureStats:
    deg_C_over_recommended: float | None
    deg_C_over_max: float | None


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

        latencies = self.__compute_latencies(task, target_node.node, ctx)
        temperatures = self.__compute_temperature_stats(task, target_node.node)

        return SchedulingResult(
            success=True,
            task=task.name,
            target_node=target_node.node.name,
            target_node_type=type(target_node.node).__name__,
            score=target_node.score,
            scheduling_duration_msec=timer.duration_ms(),
            avg_pred_latency=latencies.avg_pred_latency,
            avg_pred_latency_slo=latencies.avg_pred_latency_slo,
            avg_data_latency=latencies.avg_data_latency,
            avg_data_latency_slo=latencies.avg_data_latency_slo,
            deg_C_over_recommended=temperatures.deg_C_over_recommended,
            deg_C_over_max=temperatures.deg_C_over_max,
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


    def __compute_latencies(self, task: Task, target_node: Node, ctx: SchedulingContext) -> _TaskLatencies:
        avg_preds_latency: float | None = 0.0
        avg_preds_latency_slo: float | None = 0.0
        pred_count = 0
        for slo, pred_task, pred_node in ctx.workflow.incoming_link_slos(task):
            if not pred_node:
                raise SystemError(f'Predecessor task {pred_task.name} has not been scheduled.')
            if slo.max_latency_msec is not None:
                avg_preds_latency_slo += slo.max_latency_msec
                avg_preds_latency += ctx.orchestrator.get_latency(pred_node, target_node)
                pred_count += 1
        if pred_count > 0:
            avg_preds_latency /= float(pred_count)
            avg_preds_latency_slo /= float(pred_count)
        else:
            avg_preds_latency = None
            avg_preds_latency_slo = None

        avg_data_latency: float | None = 0.0
        avg_data_latency_slo: float | None = 0.0
        for slo in task.data_source_slos:
            if slo.max_latency_msec is not None:
                avg_data_latency += ctx.orchestrator.get_latency(slo.data_source, target_node)
                avg_data_latency_slo += slo.max_latency_msec
        data_slos_count = float(len(task.data_source_slos))
        if data_slos_count > 0:
            avg_data_latency /= data_slos_count
            avg_data_latency_slo /= data_slos_count
        else:
            avg_data_latency = None
            avg_data_latency_slo = None

        return _TaskLatencies(
            avg_pred_latency=avg_preds_latency,
            avg_pred_latency_slo=avg_preds_latency_slo,
            avg_data_latency=avg_data_latency,
            avg_data_latency_slo=avg_data_latency_slo,
        )


    def __compute_temperature_stats(self, task: Task, target_node: Node) -> _TemperatureStats:
        temperatures = _TemperatureStats(None, None)
        if not isinstance(target_node, SatelliteNode):
            return temperatures

        temperatures.deg_C_over_recommended = target_node.heat_status.temperature_C - target_node.heat_status.recommended_high_temp_C
        temperatures.deg_C_over_max = target_node.heat_status.temperature_C - target_node.heat_status.max_temp_C
        return temperatures

