import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Literal, NewType, Sequence, Union

Category = NewType("Category", str)
Timestamp = NewType("Timestamp", float)


class TraceEvent:
    """
    The Trace Event Format is the trace data representation that is processed by the Trace
    Viewer. [This document is the canonical reference on the 'Trace Event Format'](https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview?tab=t.0)
    """

    ...


class Phase(str, Enum):
    """
    The phase describes the event's type. The phase is a single character which changes depending on
    the type of event. This class encapsulates all the valid phase types.

    The following is a description of some of the valid event types:

    * Duration Events:
        Duration events provide a way of marking a duration of work on a given thread. Duration
        events are marked by the 'B' & 'E' phase types. The 'B' event must come before the 'E'
        event. 'B' & 'E' events may be nested, allowing the capturing of function calling behaviour
        on a thread. The timestamps for duration events must be in an increasing order for a given
        thread. Timestamps in different threads do not have to be in increasing order.
    * Instant Events:
        Instant events, or points in time, that correspond to an event that happens but has no
        associated duration.
    """

    B = "B"
    """Marks the beginning of a duration event."""
    E = "E"
    """Marks the end of a duration event."""
    i = "i"
    """Marks an instant event."""


@dataclass(frozen=True)
class DurationEvent: ...


@dataclass(frozen=True)
class BeginDurationEvent(DurationEvent):
    name: str
    cat: Category
    ts: Timestamp = field(default_factory=lambda: Timestamp(time.time()))
    pid: int = 1
    tid: int = 1
    args: Dict[str, Union[str, Sequence[str]]] = field(default_factory=dict)
    ph: Literal[Phase.B] = Phase.B


@dataclass(frozen=True)
class EndDurationEvent(DurationEvent):
    pid: int = 1
    tid: int = 1
    ts: Timestamp = field(default_factory=lambda: Timestamp(time.time()))
    ph: Literal[Phase.E] = Phase.E


class InstantScope(str, Enum):
    """Specifies the scope of the instant event. The scope of the event designates how tall to draw
    the instant even in Trace Viewer."""

    g = "g"
    """Global scoped instant event. A globally scoped event will draw a line from the top to the
    bottom of the timeline."""
    p = "p"
    """Process scoped instant event. A process scoped instant event will draw through all threads of
    a given process."""
    t = "t"
    """Thread scoped instant event. A thread scoped instant event will draw the height of a single
    thread."""


@dataclass(frozen=True)
class InstantEvent(TraceEvent):
    name: str
    pid: int = 1
    tid: int = 1
    ts: Timestamp = field(default_factory=lambda: Timestamp(time.time()))
    ph: Literal[Phase.i] = Phase.i
    s: InstantScope = InstantScope.t


SerializableEvent = Union[DurationEvent, InstantEvent]
