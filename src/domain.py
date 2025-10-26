from datetime import datetime
from typing import NamedTuple, TypedDict
from dataclasses import dataclass


class Events(TypedDict):
    service: str
    timestamp: float
    message: str

@dataclass
class Result:
    value: float
    newest_considered: datetime
    oldest_considered: datetime
