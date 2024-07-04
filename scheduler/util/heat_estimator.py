from scheduler.model import ResourceType, SatelliteNode, Task

class HeatEstimator:
    '''Utility for estimating the hardware temperature of a satellite during the processing of a task.'''

    def estimate_max_temp(self, node: SatelliteNode, task: Task) -> float:
        '''Estimates the maximum temperature expected during the execution time of the task.'''

        exp_runtime_msec = task.expected_exec_time_msec.get(node.cpu_arch)
        if exp_runtime_msec is None:
            return node.heat_status.temperature_C

        exp_runtime_minutes = exp_runtime_msec / 1000 / 60
        max_orbit_temp = self.__estimate_max_orbit_temp(node, exp_runtime_minutes)
        temp_increase = self.__estimate_comp_temp_increase(node, task, exp_runtime_minutes)
        return max_orbit_temp + temp_increase


    def __estimate_max_orbit_temp(self, node: SatelliteNode, exp_runtime_minutes: float) -> float:
        return int(node.heat_status.mocked_max_orbit_base_temp_C * exp_runtime_minutes) % int(node.heat_status.max_temp_C)


    def __estimate_comp_temp_increase(self, node: SatelliteNode, task: Task, exp_runtime_minutes: float) -> float:
        cpu_cores = task.req_resources.get(ResourceType.MILLI_CPU, 0) / 1000.0
        cpu_minutes = exp_runtime_minutes * cpu_cores
        exp_increase = node.heat_status.temp_inc_per_cpu_minute_C * cpu_minutes
        cooling = node.heat_status.radiated_heat_per_minute_C * exp_runtime_minutes
        return exp_increase - cooling

