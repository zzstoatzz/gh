import logging
import os
from collections import deque

from prefect.events import emit_event


class EventLogHandler(logging.Handler):
    def __init__(self, log_dir, max_buffer_size=1024 * 1024):  # 1 MB
        super().__init__()
        self.log_dir = log_dir
        self.max_buffer_size = max_buffer_size
        self.buffer = deque()
        self.buffer_size = 0
        self.counter = 0

    def emit(self, record):
        message = self.format(record)
        message_size = len(message.encode("utf-8"))

        if self.buffer_size + message_size > self.max_buffer_size:
            self.flush()
            emit_event(
                f"{self.__class__.__name__}.flushed-buffer",
                resource={
                    "prefect.resource.id": id(self),
                    "prefect.resource.name": self.__class__.__name__,
                    "prefect.resource.kind": "logging-handler",
                },
                payload={
                    "buffer_size": self.buffer_size,
                    "path": self.log_dir,
                },
            )

        self.buffer.append(message)
        self.buffer_size += message_size

    def flush(self):
        if self.buffer:
            log_file = os.path.join(self.log_dir, f"event_log_{self.counter}.log")
            with open(log_file, "w") as file:
                file.write("\n".join(self.buffer))
            self.buffer.clear()
            self.buffer_size = 0
            self.counter += 1

    def close(self):
        self.flush()
        super().close()
