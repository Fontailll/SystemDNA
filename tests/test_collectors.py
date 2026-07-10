from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from systemdna.collectors.base import Collector, CollectorResult
from systemdna.collectors.registry import CollectorRegistry
from systemdna.collectors.runner import CollectorRunner


class SimpleCollector(Collector[dict[str, str]]):
    name = "simple"
    description = "A simple test collector"

    def collect(self) -> dict[str, str]:
        return {"status": "ok"}


class FailingCollector(Collector[Any]):
    name = "failing"
    description = "A collector that always fails"

    def collect(self) -> Any:
        msg = "intentional failure"
        raise RuntimeError(msg)


class SlowCollector(Collector[Any]):
    name = "slow"
    description = "A collector that times out"

    def collect(self) -> Any:
        time.sleep(100)
        return {}


def test_registry_register_and_get() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()

    collector = SimpleCollector()
    registry.register(collector)
    assert registry.get("simple") is collector


def test_registry_get_nonexistent() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()
    assert registry.get("nonexistent") is None


def test_registry_all_order() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()

    c1 = SimpleCollector()
    c2 = FailingCollector()
    registry.register(c1)
    registry.register(c2)
    all_collectors = registry.all()
    assert all_collectors[0].name == "simple"
    assert all_collectors[1].name == "failing"


def test_registry_names() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()
    registry.register(SimpleCollector())
    assert registry.names() == ["simple"]


def test_registry_remove() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()
    c = SimpleCollector()
    registry.register(c)
    assert registry.remove("simple") is True
    assert registry.get("simple") is None


def test_registry_remove_nonexistent() -> None:
    registry = CollectorRegistry()
    assert registry.remove("nonexistent") is False


def test_registry_register_many() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()
    registry.register_many([SimpleCollector(), FailingCollector()])
    assert len(registry.all()) == 2


def test_registry_overwrite() -> None:
    registry = CollectorRegistry()
    registry._collectors.clear()
    c1 = SimpleCollector()
    c2 = SimpleCollector()
    registry.register(c1)
    registry.register(c2)
    assert registry.get("simple") is c2


def test_runner_returns_results() -> None:
    runner = CollectorRunner(timeout=5)
    results = runner.run([SimpleCollector()])
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].data == {"status": "ok"}
    assert results[0].error is None


def test_runner_failed_collectors_dont_stop_runner() -> None:
    runner = CollectorRunner(timeout=5)
    results = runner.run([SimpleCollector(), FailingCollector()])
    assert len(results) == 2
    result_map = {r.name: r for r in results}
    assert result_map["simple"].success is True
    assert result_map["failing"].success is False
    assert result_map["failing"].error is not None
    assert "RuntimeError" in result_map["failing"].error


def test_runner_with_name_filter() -> None:
    runner = CollectorRunner(timeout=5)
    results = runner.run(
        [SimpleCollector(), FailingCollector()],
        names=["simple"],
    )
    assert len(results) == 1
    assert results[0].name == "simple"


def test_runner_empty_names_returns_empty() -> None:
    runner = CollectorRunner(timeout=5)
    results = runner.run([SimpleCollector()], names=[])
    assert results == []


def test_runner_empty_collectors_returns_empty() -> None:
    runner = CollectorRunner(timeout=5)
    assert runner.run([]) == []


def test_runner_times_out_long_collectors() -> None:
    from concurrent.futures import TimeoutError as FuturesTimeoutError

    runner = CollectorRunner(timeout=0.01)
    with pytest.raises(FuturesTimeoutError):
        runner.run([SlowCollector()])


def test_runner_result_has_duration() -> None:
    runner = CollectorRunner(timeout=5)
    results = runner.run([SimpleCollector()])
    assert results[0].duration_ms >= 0


def test_runner_max_workers() -> None:
    runner = CollectorRunner(timeout=5, max_workers=1)
    results = runner.run([SimpleCollector(), FailingCollector()])
    assert len(results) == 2


def test_base_collector_interface() -> None:
    assert hasattr(SimpleCollector, "name")
    assert hasattr(SimpleCollector, "description")
    assert hasattr(SimpleCollector, "collect")


def test_collector_result_dataclass() -> None:
    result = CollectorResult(
        name="test",
        success=True,
        data={"x": 1},
        error=None,
        duration_ms=10.5,
    )
    assert result.name == "test"
    assert result.success is True
    assert result.data == {"x": 1}
    assert result.error is None
    assert result.duration_ms == 10.5


def test_collector_result_defaults() -> None:
    result = CollectorResult(name="test", success=False)
    assert result.data is None
    assert result.error is None
    assert result.duration_ms == 0.0


def test_registry_builtins_registered() -> None:
    registry = CollectorRegistry()
    names = registry.names()
    expected = {"system", "hardware", "network", "packages", "services", "users", "security", "configuration"}
    assert expected.issubset(set(names))


def test_execute_collector_exception_handling() -> None:
    runner = CollectorRunner(timeout=5)
    result = runner._execute_collector(FailingCollector())
    assert result.success is False
    assert result.error is not None
