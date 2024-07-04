from csv import DictWriter
from scheduler.scheduler import SchedulingResult

def write_results_to_csv(path: str, results: list[SchedulingResult]):
    keys = list(results[0].to_dict().keys())
    with open(path, 'w') as csv_file:
        writer = DictWriter(f=csv_file, fieldnames=keys)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())
