import json
import os
from typing import Dict, Any, Generator
# FIX: Ensure datetime is imported for use in compute
from datetime import datetime 
from src.domain import Result


def process_log(log_event: Dict[str, Any], service_metrics: Dict[str, Dict[str, int]]) -> None:
    service_name = log_event.get("service")
    message = log_event.get("message", "")

    if service_name not in service_metrics:
        service_metrics[service_name] = {
            "success_count": 0,
            "log_count": 0
        }

    # Success criteria: message contains "HTTP Status Code: 200"
    is_success = "HTTP Status Code: 200" in message

    if is_success:
        service_metrics[service_name]["success_count"] += 1

    service_metrics[service_name]["log_count"] += 1


def get_service_average(service_metrics: Dict[str, Dict[str, int]], service_name: str) -> float:
    """Calculates the success rate (float) for a specific service."""
    metrics = service_metrics.get(service_name)
    
    if not metrics:
        return 0.0
        
    count = metrics["log_count"]
    successes = metrics["success_count"]
    
    return (successes / count) if count > 0 else 0.0


def compute(data_path: str) -> Generator[Result, None, None]:
    service_metrics: Dict[str, Dict[str, int]] = {}
    processed_files = set()
    newest_timestamp = 0.0
    oldest_timestamp = float('inf')

    while True:
        try:
            current_files = set(os.listdir(data_path))
        except FileNotFoundError:
            current_files = set()
            
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
                    process_log(event, service_metrics)

                    ts = event.get("timestamp", 0.0)
                    if ts > newest_timestamp:
                        newest_timestamp = ts
                    if ts < oldest_timestamp and ts != 0.0:
                        oldest_timestamp = ts

                processed_files.add(file_name)

            average_value = get_service_average(service_metrics, "monitoring") 
            
            newest_dt = datetime.fromtimestamp(newest_timestamp)
            oldest_dt = datetime.fromtimestamp(oldest_timestamp)

            yield Result(
                value=average_value,
                newest_considered=newest_dt,
                oldest_considered=oldest_dt,
            )


if __name__ == "__main__":
    DATA_DIRECTORY = r"C:\Users\ASUS\Documents\Maestria Ciencia de los Datos\TERCER SEMESTRE\MINERIA DE GRANDES VOLUMENES INFO\TALLER 5\data"
    generator = compute(DATA_DIRECTORY)
    first_result = next(generator) 
    print(f"Result 1 Value: {first_result.value * 100:.2f}%")
        
    next(generator)
