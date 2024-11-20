"""
The pytest-perfetto plugin aims to help developers profile their tests by ultimately producing a
'perfetto' trace file, which may be natively visualized using most Chromium-based browsers.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Literal, NewType, Optional, Tuple

import pytest

Category = NewType("Category", str)
Timestamp = NewType("Timestamp", float)


class TraceEvent:
    """
    The Trace Event Format is the trace data representation that is processed byt he Trace
    Viewer. [This document is the canonical reference on the 'Trace Event Format'](https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview?tab=t.0)
    """

    ...


class Phase(str, Enum):
    """
    The phase described the event type. This is a single character which changes depending on the
    type of event being output. This class will encapsulate all the valid phase types

    The following is a description of some of the valid event types:

    * Duration Events:
        Duration events provide a way to mark a duration of work on a given thread. Duration events
        are marked by the 'B' & 'E' phase types. The 'B' event must come before the 'E' event. 'B' &
        'E' events may be nested, allowing the capturing of function calling behaviour on a thread.
        The timestamps for duration events must be in an increasing order for a given thread.
        Timestamps in different threads do not have to be in increasing order.
    """

    B = "B"
    """Marks the beginning of a duration event."""
    E = "E"
    """Marks the end of a duration event"""


@dataclass(frozen=True)
class DurationEvent: ...


@dataclass(frozen=True)
class BeginDurationEvent(DurationEvent):
    name: str
    cat: Category
    ts: Timestamp = field(default_factory=lambda: Timestamp(time.monotonic()))
    pid: int = 1
    tid: int = 1
    args: Dict[str, Any] = field(default_factory=dict)
    ph: Literal[Phase.B] = Phase.B


@dataclass(frozen=True)
class EndDurationEvent(DurationEvent):
    pid: int = 1
    tid: int = 1
    ts: Timestamp = field(default_factory=lambda: Timestamp(time.monotonic()))
    ph: Literal[Phase.E] = Phase.E


events: List[DurationEvent] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionstart() -> Generator[None, None, None]:
    # Called after the `Session` object has been created and before performing collection and
    # entering the run test loop.
    events.append(
        BeginDurationEvent(
            name="pytest session",
            cat=Category("pytest"),
        )
    )
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_sessionfinish(session: pytest.Session) -> Generator[None, None, None]:
    # Called after whole test run finished, right before returning the exit status to the system
    # https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest.hookspec.pytest_sessionfinish
    events.append(EndDurationEvent())
    with Path(f"{session.startpath}/trace.json").open("w") as file:
        json.dump([asdict(event) for event in events], file)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_collection() -> Generator[None, None, None]:
    events.append(
        BeginDurationEvent(
            name="Start Collection",
            cat=Category("pytest"),
        )
    )
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_finish() -> Generator[None, None, None]:
    events.append(EndDurationEvent())
    yield


# ===== Test running (runtest) hooks =====
# https://docs.pytest.org/en/7.1.x/reference/reference.html#test-running-runtest-hooks


def create_args_from_location(location: Tuple[str, Optional[int], str]) -> Dict[str, str]:
    (file_name, line_number, test_name) = location

    args = {"file_name": file_name, "test_name": test_name}

    if line_number is not None:
        args["line_number"] = str(line_number)

    return args


def pytest_runtest_logstart(nodeid: str, location: Tuple[str, Optional[int], str]) -> None:
    events.append(
        BeginDurationEvent(
            name=nodeid,
            args=create_args_from_location(location),
            cat=Category("test"),
        )
    )


def pytest_runtest_logfinish() -> None:
    events.append(EndDurationEvent())
