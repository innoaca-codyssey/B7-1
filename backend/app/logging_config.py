import json
import logging

logger = logging.getLogger("app")


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _format_value(value) -> str:
    text = str(value)
    if text == "" or any(c.isspace() or c in '="' for c in text):
        return json.dumps(text, ensure_ascii=False)
    return text


def log_event(event: str, level: int = logging.INFO, **fields) -> None:
    logger.log(level, " ".join([event, *(f"{k}={_format_value(v)}" for k, v in fields.items())]))
