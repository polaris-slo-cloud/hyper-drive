
from time import perf_counter_ns


class Timer:

    def __init__(self):
        self.start_ns: int = 0
        self.stop_ns: int = 0

    def start(self):
        self.start_ns = perf_counter_ns()
    
    def stop(self):
        self.stop_ns = perf_counter_ns()
    
    def duration_ms(self) -> int:
        duration = (self.stop_ns - self.start_ns) / 1000000
        return int(duration)