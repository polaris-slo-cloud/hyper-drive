from dataclasses import dataclass
from scheduler.model import CpuArchitecture, DataSourceSLO, NetworkSLO, Node, PredecessorConfig, ResourceType, Task, Workflow

@dataclass
class WildfireDetectionWorkflow:
    wf: Workflow
    ingest_task: Task
    extract_frames_task: Task
    object_det_task: Task
    prepare_ds_task: Task
    last_scheduled_task: Task | None = None

    def get_next_task(self) -> Task:
        if self.last_scheduled_task:
            return self.wf.get_successors(self.last_scheduled_task)[0]
        return self.ingest_task


def create_wildfire_detection_wf(eo_sat_node: Node) -> WildfireDetectionWorkflow:
    '''
    Creates a workflow for the wildfire detection use case.
    '''
    wf = Workflow()

    ingest_task = Task(
        name='ingest',
        image='polarissloc/wildfire-det-ingest',
        cpu_archs=[ CpuArchitecture.ARM64 ],
        req_resources={
            ResourceType.MILLI_CPU: 1000,
            ResourceType.MEMORY_MIB: 2048,
        },
        data_source_slos=None,
        expected_exec_time_msec=None,
    )
    wf.add_task(ingest_task)

    extract_frames_task = Task(
        name='extract-frames',
        image='polarissloc/wildfire-det-extract-frames',
        cpu_archs=[ CpuArchitecture.ARM64, CpuArchitecture.INTEL64 ],
        req_resources={
            ResourceType.MILLI_CPU: 4000,
            ResourceType.MEMORY_MIB: 2048,
        },
        data_source_slos=None,
        expected_exec_time_msec={
            CpuArchitecture.ARM64: 60000,
            CpuArchitecture.INTEL64: 50000,
        },
    )
    extract_frames_pred_conf = PredecessorConfig(
        ingest_task,
        NetworkSLO(max_latency_msec=100, min_bandwidth_kpbs=None)
    )
    wf.add_task(extract_frames_task, [ extract_frames_pred_conf ])

    object_det_task = Task(
        name='object-det',
        image='polarissloc/wildfire-det-object_det',
        cpu_archs=[ CpuArchitecture.ARM64, CpuArchitecture.INTEL64 ],
        req_resources={
            ResourceType.MILLI_CPU: 4000,
            ResourceType.MEMORY_MIB: 2048,
        },
        data_source_slos=[
            DataSourceSLO(data_source=eo_sat_node, max_latency_msec=150, min_bandwidth_kpbs=None)
        ],
        expected_exec_time_msec={
            CpuArchitecture.ARM64: 600000,
            CpuArchitecture.INTEL64: 500000,
        },
    )
    object_det_pred_conf = PredecessorConfig(
        extract_frames_task,
        NetworkSLO(max_latency_msec=150, min_bandwidth_kpbs=None)
    )
    wf.add_task(object_det_task, [ object_det_pred_conf ])

    prepare_ds_task = Task(
        name='prepare-ds',
        image='polarissloc/wildfire-det-prepare-ds',
        cpu_archs=[ CpuArchitecture.ARM64, CpuArchitecture.INTEL64 ],
        req_resources={
            ResourceType.MILLI_CPU: 4000,
            ResourceType.MEMORY_MIB: 4096,
        },
        data_source_slos=None,
        expected_exec_time_msec={
            CpuArchitecture.ARM64: 90000,
            CpuArchitecture.INTEL64: 80000,
        },
    )
    prepare_ds_pred_conf = PredecessorConfig(
        object_det_task,
        NetworkSLO(max_latency_msec=250, min_bandwidth_kpbs=None)
    )
    wf.add_task(prepare_ds_task, [ prepare_ds_pred_conf ])

    return WildfireDetectionWorkflow(
        wf=wf,
        ingest_task=ingest_task,
        extract_frames_task=extract_frames_task,
        object_det_task=object_det_task,
        prepare_ds_task=prepare_ds_task,
    )
