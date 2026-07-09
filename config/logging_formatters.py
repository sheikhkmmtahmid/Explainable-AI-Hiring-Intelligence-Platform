"""
JSON log formatter for production. Most log aggregation tools (CloudWatch,
Datadog, ELK, whatever a real deployment ends up using) expect one JSON
object per line so they can parse and alert on fields directly, rather than
regex-parsing free text. Written by hand rather than pulling in a
dependency (python-json-logger or similar) since the actual formatting
logic needed here is small and this avoids one more third-party package to
track.
"""
import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Anything passed via logger.info(..., extra={...}) rides along too.
        for key, value in record.__dict__.items():
            if key not in payload and key not in (
                "args", "msg", "levelno", "levelname", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
            ):
                try:
                    json.dumps(value)
                    payload[key] = value
                except TypeError:
                    payload[key] = str(value)
        return json.dumps(payload)
