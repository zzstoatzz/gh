import logging

from prefect.events import emit_event


class EventLogHandler(logging.Handler):
    def emit(self, record):
        message = self.format(record)

        emit_event(
            f"memory.logged.{record.levelname.lower()}",
            resource={"prefect.resource.id": id(message)},
            payload={"message": message},
        )
