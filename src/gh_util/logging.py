"""Module for logging utilities."""

import logging
from functools import lru_cache, partial

from rich.logging import RichHandler
from rich.markup import escape

import gh_util


@lru_cache()
def get_logger(
    name: str | None = None,
) -> logging.Logger:
    """
    Retrieves a logger with the given name, or the root logger if no name is given.

    Args:
        name: The name of the logger to retrieve.

    Returns:
        The logger with the given name, or the root logger if no name is given.

    Example:
        Basic Usage of `get_logger`
        ```python
        from gh_util.utilities.logging import get_logger

        logger = get_logger("gh_util.test")
        logger.info("This is a test") # Output: gh_util.test: This is a test

        debug_logger = get_logger("gh_util.debug")
        debug_logger.debug_kv("TITLE", "log message", "green")
        ```
    """
    parent_logger = logging.getLogger("gh_util")

    if name:
        if not name.startswith(parent_logger.name + "."):
            logger = parent_logger.getChild(name)
        else:
            logger = logging.getLogger(name)
    else:
        logger = parent_logger

    add_logging_methods(logger)
    return logger


def setup_logging(
    level: str | None = None,
) -> None:
    logger = get_logger()

    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(gh_util.settings.log_level)

    logger.handlers.clear()

    handler = RichHandler(rich_tracebacks=True, markup=False)
    formatter = logging.Formatter("%(name)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False


def add_logging_methods(logger: logging.Logger) -> None:
    def log_style(level: int, message: str, style: str | None = None):
        if not style:
            style = "default on default"
        message = f"[{style}]{escape(str(message))}[/]"
        logger.log(level, message, extra={"markup": True})

    def log_kv(
        level: int,
        key: str,
        value: str,
        key_style: str = "default on default",
        value_style: str = "default on default",
        delimiter: str = ": ",
    ):
        logger.log(
            level,
            f"[{key_style}]{escape(str(key))}{delimiter}[/][{value_style}]{escape(str(value))}[/]",
            extra={"markup": True},
        )

    setattr(logger, "debug_style", partial(log_style, logging.DEBUG))
    setattr(logger, "info_style", partial(log_style, logging.INFO))
    setattr(logger, "warning_style", partial(log_style, logging.WARNING))
    setattr(logger, "error_style", partial(log_style, logging.ERROR))
    setattr(logger, "critical_style", partial(log_style, logging.CRITICAL))

    setattr(logger, "debug_kv", partial(log_kv, logging.DEBUG))
    setattr(logger, "info_kv", partial(log_kv, logging.INFO))
    setattr(logger, "warning_kv", partial(log_kv, logging.WARNING))
    setattr(logger, "error_kv", partial(log_kv, logging.ERROR))
    setattr(logger, "critical_kv", partial(log_kv, logging.CRITICAL))
