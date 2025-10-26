import datetime
import json
import pathlib

from src import domain
from src.task_1 import compute
from src.domain import Result

def test_task_1(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=48)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200", # Success 1
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=96)
                    ).timestamp(),
                    "message": "HTTP Status Code: 500", # Failure 1
                },
            ],
            file,
        )

    # Initialize the generator
    generator = compute(str(source))
    
    # Process BATCH 1 -> (1 success / 2 total) = 0.5
    first = next(generator)

    # --- BATCH 2: Create the second file with 1 log ---
    with open(source / "batch_2.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=144)
                    ).timestamp(),
                    "message": "HTTP Status Code: 200", # Success 2
                },
            ],
            file,
        )

    second = next(generator)

    assert first.value == 0.5
    assert first.newest_considered.timestamp() == (basetime + datetime.timedelta(seconds=96)).timestamp()
    assert first.oldest_considered.timestamp() == (basetime + datetime.timedelta(seconds=48)).timestamp()

    assert first == Result(
        value=0.5,
        newest_considered=basetime + datetime.timedelta(seconds=96),
        oldest_considered=basetime + datetime.timedelta(seconds=48),
    )

    assert second.value == (2/3) 
    assert second.newest_considered.timestamp() == (basetime + datetime.timedelta(seconds=144)).timestamp()
    assert second.oldest_considered.timestamp() == (basetime + datetime.timedelta(seconds=48)).timestamp()
    assert second == Result(
        value=(2/3), 
        newest_considered=basetime + datetime.timedelta(seconds=144),
        oldest_considered=basetime + datetime.timedelta(seconds=48),
    )
    
