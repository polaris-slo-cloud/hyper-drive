from scheduler.pipeline import CommitPlugin, FilterPlugin, ScorePlugin, SelectCandidateNodesPlugin
from scheduler.plugins import MultiCommitPlugin, NetworkQosPlugin, ResourcesFitPlugin, SelectNodesInVicinityPlugin

def create_default_candidate_nodes_plugin() -> SelectCandidateNodesPlugin:
    return SelectNodesInVicinityPlugin()


def create_default_filter_plugins() -> list[FilterPlugin]:
    return [
        ResourcesFitPlugin(),
        NetworkQosPlugin(),
    ]


def create_default_score_plugins() -> list[ScorePlugin]:
    return [
        NetworkQosPlugin(),
    ]


def create_default_commit_plugin() -> CommitPlugin:
    return MultiCommitPlugin()
