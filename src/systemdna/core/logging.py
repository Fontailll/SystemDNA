from __future__ import annotations

import logging
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

_level_map: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class Logger:
    def __init__(
        self,
        name: str = "systemdna",
        level: str = "WARNING",
        log_file: Path | None = None,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(_level_map.get(level.upper(), logging.WARNING))
        self._logger.handlers.clear()
        self._add_console_handler()
        self._file_handler: logging.FileHandler | None = None
        if log_file is not None:
            self._add_file_handler(log_file)

    def _add_console_handler(self) -> None:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        self._logger.addHandler(handler)

    def _add_file_handler(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        self._logger.addHandler(handler)
        self._file_handler = handler

    def set_level(self, level: str) -> None:
        self._logger.setLevel(_level_map.get(level.upper(), logging.WARNING))

    def debug(self, message: str, *args: object) -> None:
        self._logger.debug(message, *args)

    def info(self, message: str, *args: object) -> None:
        self._logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        self._logger.error(message, *args)

    def critical(self, message: str, *args: object) -> None:
        self._logger.critical(message, *args)

    def add_file_output(self, path: Path) -> None:
        if self._file_handler is not None:
            self._logger.removeHandler(self._file_handler)
        self._add_file_handler(path)

    def remove_file_output(self) -> None:
        if self._file_handler is not None:
            self._logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None
