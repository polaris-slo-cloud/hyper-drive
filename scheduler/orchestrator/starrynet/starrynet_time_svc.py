

class StarryNetTimeService:
    '''Manages the internal clock of StarryNet.'''

    def __init__(self):
        self.__curr_time: int = 0

    @property
    def curr_time(self) -> int:
        '''Gets the current StarryNet time index.'''
        return self.__curr_time

    def increment_clock(self) -> int:
        '''Increments the current time by 1 and returns the new value.'''
        self.__curr_time += 1
        return self.__curr_time
