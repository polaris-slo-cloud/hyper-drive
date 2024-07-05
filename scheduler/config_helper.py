from scheduler.pipeline import CommitPlugin, FilterPlugin, ScorePlugin, SelectCandidateNodesPlugin
from scheduler.plugins import HeatOptPlugin, MultiCommitPlugin, NetworkQosPlugin, ResourcesFitPlugin, SelectNodesInVicinityPlugin

def create_default_candidate_nodes_plugin() -> SelectCandidateNodesPlugin:
    return SelectNodesInVicinityPlugin(
        radius_ground_km=500.0,
        radius_edge_km=200,
        radius_space_km=2000,
        ground_nodes_count=120,
        edge_nodes_count=120,
        space_nodes_count=60,
    )


def create_default_filter_plugins() -> list[FilterPlugin]:
    return [
        ResourcesFitPlugin(),
        NetworkQosPlugin(),
    ]


def create_default_score_plugins() -> list[ScorePlugin]:
    return [
        NetworkQosPlugin(),
        HeatOptPlugin(),
    ]


def create_default_commit_plugin() -> CommitPlugin:
    return MultiCommitPlugin()
