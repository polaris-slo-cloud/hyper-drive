from scheduler.model import CpuArchitecture, DataSourceSLO, NetworkSLO, Node, PredecessorConfig, ResourceType, Task, Workflow


def create_wildfire_detection_wf(eo_sat_node: Node) -> Workflow:
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
            DataSourceSLO(data_source=eo_sat_node, max_latency_msec=80, min_bandwidth_kpbs=None)
        ],
        expected_exec_time_msec={
            CpuArchitecture.ARM64: 180000,
            CpuArchitecture.INTEL64: 170000,
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

    return wf
