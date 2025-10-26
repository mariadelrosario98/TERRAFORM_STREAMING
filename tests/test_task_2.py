import datetime
import json
import pathlib
import pytest 
from src.task_2 import compute
from src.domain import Result


def test_task_2_sliding_window(tmp_path: pathlib.Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True, exist_ok=True)
    basetime = datetime.datetime.now()
    
    WINDOW_SECONDS = 60 
    with open(source / "batch_1.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=30) 
                    ).timestamp(),
                    "message": "HTTP Status Code: 200", 
                },
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=90) 
                    ).timestamp(),
                    "message": "HTTP Status Code: 500", 
                },
            ],
            file,
        )

    generator = compute(str(source))
    first = next(generator) 

    with open(source / "batch_2.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=100)
                    ).timestamp(),
                    "message": "HTTP Status Code: 503", 
                },
            ],
            file,
        )

    next(generator) 
    second = next(generator) 

    with open(source / "batch_3.json", "w") as file:
        json.dump(
            [
                {
                    "service": "monitoring",
                    "timestamp": (
                        basetime + datetime.timedelta(seconds=155) 
                    ).timestamp(),
                    "message": "HTTP Status Code: 200", 
                },
            ],
            file,
        )
    
    next(generator)
    third = next(generator) 

    assert first.value == 1.0 
    assert first.newest_considered.timestamp() == (basetime + datetime.timedelta(seconds=90)).timestamp()
    assert first.oldest_considered.timestamp() == (basetime + datetime.timedelta(seconds=30)).timestamp() 
    assert first == Result(
        value=1.0, 
        newest_considered=basetime + datetime.timedelta(seconds=90),
        oldest_considered=basetime + datetime.timedelta(seconds=30),
    )

    assert second.value == 2.0 
    assert second.newest_considered.timestamp() == (basetime + datetime.timedelta(seconds=100)).timestamp()
    assert second.oldest_considered.timestamp() == (basetime + datetime.timedelta(seconds=40)).timestamp() 
    assert second == Result(
        value=2.0, 
        newest_considered=basetime + datetime.timedelta(seconds=100),
        oldest_considered=basetime + datetime.timedelta(seconds=40),
    )

    assert third.value == 1.0 
    assert third.newest_considered.timestamp() == (basetime + datetime.timedelta(seconds=155)).timestamp()
    assert third.oldest_considered.timestamp() == (basetime + datetime.timedelta(seconds=95)).timestamp() 
    assert third == Result(
        value=1.0, 
        newest_considered=basetime + datetime.timedelta(seconds=155),
        oldest_considered=basetime + datetime.timedelta(seconds=95),
    )