import json
import os
import time
from typing import Dict, Any, Generator, List, Tuple
from datetime import datetime, timedelta
from src.domain import Result

# The sliding window is 60 seconds (1 minute)
SLIDING_WINDOW_SECONDS = 60


def is_failure(log_event: Dict[str, Any]) -> bool:
    message = log_event.get("message", "")
    return "HTTP Status Code: 200" not in message


ServiceMetrics = Dict[str, List[Tuple[float, Dict[str, Any]]]]


def compute(data_path: str) -> Generator[Result, None, None]:
    failure_window: ServiceMetrics = {}
    processed_files = set()
    newest_timestamp = 0.0
    oldest_timestamp = float('inf')

    while True:
        # Get list of files in directory
        current_files = set(os.listdir(data_path))
        new_files = sorted(list(current_files - processed_files))

        if new_files:
            for file_name in new_files:
                file_path = os.path.join(data_path, file_name)

                try:
                    with open(file_path, 'r') as f:
                        log_events = json.load(f)
                except Exception:
                    continue

                if not isinstance(log_events, list):
                    log_events = [log_events]

                for event in log_events:
                    ts = event.get("timestamp", 0.0)
                    service_name = event.get("service")

                    if ts > newest_timestamp:
                        newest_timestamp = ts
                    if ts < oldest_timestamp and ts != 0.0:
                        oldest_timestamp = ts

                    if service_name and is_failure(event):
                        if service_name not in failure_window:
                            failure_window[service_name] = []
                        failure_window[service_name].append((ts, event))

                processed_files.add(file_name)

            # Compute sliding window statistics
            window_end_time = newest_timestamp
            window_start_time = window_end_time - SLIDING_WINDOW_SECONDS
            total_failures_in_window = 0

            for service in failure_window:
                failure_window[service] = [
                    (ts, event)
                    for ts, event in failure_window[service]
                    if ts >= window_start_time
                ]
                total_failures_in_window += len(failure_window[service])

            monitoring_failures_count = len(failure_window.get("monitoring", []))
            average_value = float(monitoring_failures_count)

            newest_dt = datetime.fromtimestamp(newest_timestamp)
            oldest_dt = datetime.fromtimestamp(window_start_time)

            yield Result(
                value=average_value,
                newest_considered=newest_dt,
                oldest_considered=oldest_dt,
            )

        yield

if __name__ == "__main__":
    DATA_DIRECTORY = r"C:\Users\ASUS\Documents\Maestria Ciencia de los Datos\TERCER SEMESTRE\MINERIA DE GRANDES VOLUMENES INFO\TALLER 5\data"
    basetime = datetime.now()
    generator = compute(DATA_DIRECTORY)

    batch_1_data = [
        {"service": "monitoring", "timestamp": (basetime + timedelta(seconds=30)).timestamp(), "message": "HTTP Status Code: 200"}, 
        {"service": "monitoring", "timestamp": (basetime + timedelta(seconds=90)).timestamp(), "message": "HTTP Status Code: 500"}, 
    ]
    with open(os.path.join(DATA_DIRECTORY, "batch_1.json"), "w") as f:
        json.dump(batch_1_data, f)

    first_result = next(generator) 
    
    print(f"Run 1: {int(first_result.value)} failures in the last minute.")
    
    next(generator) 
    

    batch_2_data = [
        {"service": "monitoring", "timestamp": (basetime + timedelta(seconds=100)).timestamp(), "message": "HTTP Status Code: 503"}, # Failure 2
    ]
    with open(os.path.join(DATA_DIRECTORY, "batch_2.json"), "w") as f:
        json.dump(batch_2_data, f)
        
    second_result = next(generator) 
    
    print(f"Run 2: {int(second_result.value)} failures in the last minute.") 

    os.remove(os.path.join(DATA_DIRECTORY, "batch_1.json"))
    os.remove(os.path.join(DATA_DIRECTORY, "batch_2.json"))
