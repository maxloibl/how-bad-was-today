"""Structured JSON logging.

Log lines are emitted as single-line JSON objects. Raw article text, prompts,
and third-party full texts must never be included in log messages. As a
defence-in-depth safeguard, the formatter redacts known content-bearing fields
and never emits raw tracebacks (which could embed source content): only the
exception type and a short, truncated message are serialised.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

_REDACTED = "<redacted>"
_MAX_EXC_MESSAGE_CHARS = 200

#: Credential-bearing URL userinfo, e.g. ``postgresql+asyncpg://user:pass@host``.
_CREDENTIAL_URL = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*://)[^@\s/]+@")
#: ``password=…`` / ``token: …`` style assignments.
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\b(\s*[=:]\s*)\S+"
)

#: Field names that may carry article text, prompts, or third-party full text.
_CONTENT_KEYS = frozenset(
    {
        "body_text",
        "prompt",
        "content",
        "full_text",
        "article_text",
        "raw_text",
    }
)

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Only technical metadata is serialised. Extra fields whose key names are
    known content-bearing fields are redacted, and exception info is reduced to
    the exception type plus a short safe message rather than a full traceback.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_credentials(self._sanitize_message(record.getMessage())),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            if key in _CONTENT_KEYS:
                payload[key] = _REDACTED
            elif isinstance(value, str):
                payload[key] = _redact_credentials(value)
            else:
                payload[key] = value

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            exc_message = str(exc_value) if exc_value is not None else ""
            payload["exc_type"] = exc_type.__name__ if exc_type is not None else None
            payload["exc_message"] = _redact_credentials(self._sanitize_message(exc_message))[
                :_MAX_EXC_MESSAGE_CHARS
            ]

        return json.dumps(payload, default=str, ensure_ascii=False)

    @staticmethod
    def _sanitize_message(message: str) -> str:
        """Redact a message that embeds a known content-bearing key name."""
        if any(key in message for key in _CONTENT_KEYS):
            return _REDACTED
        return message


def _redact_credentials(text: str) -> str:
    """Strip credentials from URLs and ``key=value`` assignments in ``text``.

    Connection strings and secrets routinely surface inside exception messages;
    the formatter removes them before serialising so a misconfigured
    ``DATABASE_URL`` can never leak a password into the logs.
    """
    text = _CREDENTIAL_URL.sub(r"\1<redacted>@", text)
    return _SECRET_ASSIGNMENT.sub(r"\1\2<redacted>", text)


def configure_logging(level: str = "INFO") -> None:
    """Attach a JSON formatter to the root logger's stream handler."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]
