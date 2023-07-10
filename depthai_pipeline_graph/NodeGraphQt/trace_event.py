from enum import Enum

class EventEnum(Enum):
    SEND = 0
    RECEIVE = 1
    PULL = 2

class StatusEnum(Enum):
    START = 0
    END = 1
    TIMEOUT = 2

class TraceEvent():
    event: EventEnum
    status: StatusEnum
    src_id: str
    dst_id: str
    timestamp = 0.0
    host_timestamp = 0.0
    queue_size: str

class NodeTraceEvent():
    node_id: str
    time_to_get = 0.0
    time_to_process = 0.0
    time_to_send = 0.0
    time_total = 0.0


