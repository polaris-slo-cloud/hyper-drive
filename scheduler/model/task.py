from typing import Sequence, cast
from .resources import CpuArchitecture, ResourceType
from .slos import DataSourceSLO

class Task:
    '''
    Represents a single task to be scheduled.
    '''

    def __init__(
            self,
            name: str,
            image: str,
            req_resources: dict[ResourceType, int],
            cpu_archs: list[CpuArchitecture],
            data_source_slos: Sequence[DataSourceSLO] | None,
        ):
        if name is None or name == '':
            raise ValueError('name cannot be empty')
        self.name = name
        '''The name of this task (unique within a workflow).'''

        self.image = image
        '''The container image for this task.'''

        if req_resources is None or len(req_resources) == 0:
            raise ValueError('req_resources must not be empty')
        self.req_resources = req_resources
        '''
        The dictionary of resources required by this task.
        The required quantity of each resource in this dictionary is interpreted as a minimum quantity,
        i.e., a node is eligible for hosting the task if it has at least this amount of the resource available.

        See the ResourceType enum for a list of available resource types.
        Note that not every task requires every type of resource.
        '''

        self.cpu_architectures = cpu_archs
        '''The CPU architectures supported by the container image of this task.'''

        if data_source_slos is None:
            data_source_slos = []
        self.data_source_slos: Sequence[DataSourceSLO] = data_source_slos
        '''
        The network SLOs for the connection from data sources.
        '''


    def __hash__(self) -> int:
        return self.name.__hash__();


    def __eq__(self, value: object) -> bool:
        if self is value:
            return True
        if type(value) != type(self):
            return False

        other = cast(Task, value)
        if self.name != other.name:
            return False
        if self.image != other.image:
            return False
        if self.req_resources != other.req_resources:
            return False
        if self.cpu_architectures != other.cpu_architectures:
            return False
        if self.data_source_slos != other.data_source_slos:
            return False
        return True


    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)
