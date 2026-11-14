import json
import logging
import sys

from daily_signal.core.logging import JsonFormatter


def _format(record: logging.LogRecord) -> dict[str, object]:
    return json.loads(JsonFormatter().format(record))


def test_technical_metadata_is_preserved() -> None:
    record = logging.LogRecord(
        name="daily_signal.ingestion",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="processed %d items",
        args=(5,),
        exc_info=None,
    )
    payload = _format(record)
    assert payload["message"] == "processed 5 items"
    assert payload["logger"] == "daily_signal.ingestion"
    assert payload["level"] == "INFO"


def test_content_bearing_extra_fields_are_redacted() -> None:
    record = logging.LogRecord(
        name="daily_signal.ingestion",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="item ingested",
        args=None,
        exc_info=None,
    )
    record.body_text = "FULL ARTICLE TEXT THAT MUST NOT APPEAR"
    record.prompt = "SYSTEM PROMPT THAT MUST NOT APPEAR"
    record.item_id = "abc-123"

    payload = _format(record)

    assert payload["body_text"] == "<redacted>"
    assert payload["prompt"] == "<redacted>"
    assert payload["item_id"] == "abc-123"
    serialized = json.dumps(payload)
    assert "FULL ARTICLE TEXT" not in serialized
    assert "SYSTEM PROMPT" not in serialized


def test_message_embedding_content_key_is_redacted() -> None:
    record = logging.LogRecord(
        name="daily_signal.ingestion",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="raw_text: ARTICLE BODY THAT MUST NOT APPEAR",
        args=None,
        exc_info=None,
    )
    payload = _format(record)
    assert payload["message"] == "<redacted>"


def test_exception_info_is_redacted_to_type_and_short_message() -> None:
    try:
        raise ValueError("secret third-party full text leaked in exception detail")
    except ValueError:
        record = logging.LogRecord(
            name="daily_signal.pipeline",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="pipeline failed",
            args=None,
            exc_info=sys.exc_info(),
        )

    payload = _format(record)
    assert payload["exc_type"] == "ValueError"
    assert isinstance(payload["exc_message"], str)
    assert len(payload["exc_message"]) <= 200
    # No raw traceback (frame paths / line numbers) is ever serialised.
    serialized = json.dumps(payload)
    assert "Traceback" not in serialized
    assert __file__ not in serialized


def test_credentials_in_urls_are_redacted_from_messages() -> None:
    record = logging.LogRecord(
        name="daily_signal.core.config",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="cannot connect to postgresql+asyncpg://daily_signal:s3cret@db:5432/daily_signal",
        args=None,
        exc_info=None,
    )
    payload = _format(record)
    assert "s3cret" not in json.dumps(payload)
    assert payload["message"] == (
        "cannot connect to postgresql+asyncpg://<redacted>@db:5432/daily_signal"
    )


def test_credentials_in_exception_messages_are_redacted() -> None:
    try:
        raise RuntimeError("could not connect: password=hunter2 host=db")
    except RuntimeError:
        record = logging.LogRecord(
            name="daily_signal.core.config",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="configuration error",
            args=None,
            exc_info=sys.exc_info(),
        )

    payload = _format(record)
    assert "hunter2" not in json.dumps(payload)
    assert "password=<redacted>" in payload["exc_message"]


def test_configure_logging_attaches_json_formatter() -> None:
    from daily_signal.core.logging import configure_logging

    configure_logging(level="DEBUG")
    root = logging.getLogger()
    assert any(isinstance(h.formatter, JsonFormatter) for h in root.handlers)
