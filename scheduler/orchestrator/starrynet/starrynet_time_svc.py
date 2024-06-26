from typing import Callable

SimulationAction = Callable[[int], None]
'''
An action to be called at a specific time index during the simulation.
The argument to the function is the time index.
'''

class StarryNetTimeService:
    '''Manages the internal clock of StarryNet.'''

    def __init__(self, sim_duration: int):
        self.__curr_time: int = 0
        self.__sim_duration = sim_duration

    @property
    def curr_time(self) -> int:
        '''Gets the current StarryNet time index.'''
        return self.__curr_time


    @property
    def sim_duration(self) -> int:
        '''Gets the total (planned) duration of the simulation.'''
        return self.__sim_duration


    def increment_clock(self) -> int:
        '''
        Increments the current time by 1 and returns the new value.
        Once the simulation should end, the return value is -1.
        '''
        self.__curr_time += 1
        if self.__curr_time <= self.__sim_duration:
            return self.__curr_time
        else:
            return -1


    def run_simulation(self, actions: dict[int, SimulationAction]):
        '''
        Runs the entire simulation form start to finish and calls the specified actions at the respective time indices.

        Each key in the `actions` dict specifies a time index and the respective value is a function that is called at that time.
        '''
        curr_time = 0
        while curr_time != -1:
            print(f'Experiment clock at {curr_time}')
            action = actions.get(curr_time)
            if action:
                action(curr_time)
            curr_time = self.increment_clock()

