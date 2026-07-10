from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from systemdna.collectors.base import Collector, CollectorResult

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS: float = 30.0


class CollectorRunner:
    """Runs collectors concurrently with per-collector timeout protection."""

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
        max_workers: int | None = None,
    ) -> None:
        self._timeout = timeout
        self._max_workers = max_workers

    def _execute_collector(self, collector: Collector[Any]) -> CollectorResult:
        """Run a single collector and capture timing and errors."""
        start = time.monotonic()
        try:
            data = collector.collect()
            elapsed_ms = (time.monotonic() - start) * 1000
            return CollectorResult(
                name=collector.name,
                success=True,
                data=data,
                error=None,
                duration_ms=round(elapsed_ms, 2),
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.warning("Collector '%s' failed: %s", collector.name, error_msg)
            return CollectorResult(
                name=collector.name,
                success=False,
                data=None,
                error=error_msg,
                duration_ms=round(elapsed_ms, 2),
            )

    def run(
        self,
        collectors: list[Collector[Any]],
        names: list[str] | None = None,
    ) -> list[CollectorResult]:
        """Run collectors in parallel and return results.

        Args:
            collectors: Full list of available collectors.
            names: Optional subset of collector names to run. If None, runs all.

        Returns:
            List of CollectorResult for every requested collector.
        """
        if names is not None:
            name_set = set(names)
            selected = [c for c in collectors if c.name in name_set]
        else:
            selected = list(collectors)

        if not selected:
            return []

        results: list[CollectorResult] = []
        if self._max_workers:
            worker_count = min(len(selected), self._max_workers)
        else:
            worker_count = len(selected)

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_collector = {
                executor.submit(self._execute_collector, collector): collector
                for collector in selected
            }
            for future in as_completed(future_to_collector, timeout=self._timeout):
                collector = future_to_collector[future]
                try:
                    result = future.result(timeout=0)
                    results.append(result)
                except Exception as exc:
                    error_msg = f"{type(exc).__name__}: {exc}"
                    logger.error(
                        "Collector '%s' produced an unexpected error: %s",
                        collector.name,
                        error_msg,
                    )
                    results.append(
                        CollectorResult(
                            name=collector.name,
                            success=False,
                            data=None,
                            error=error_msg,
                            duration_ms=0.0,
                        )
                    )

        result_map = {r.name: r for r in results}
        ordered_results: list[CollectorResult] = []
        for collector in selected:
            if collector.name in result_map:
                ordered_results.append(result_map[collector.name])

        return ordered_results
