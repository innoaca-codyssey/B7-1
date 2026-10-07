import logging

logger = logging.getLogger("app")


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def log_event(event: str, level: int = logging.INFO, **fields) -> None:
    logger.log(level, " ".join([event, *(f"{k}={v}" for k, v in fields.items())]))
