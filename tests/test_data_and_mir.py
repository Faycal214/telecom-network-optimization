from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from telecom_network_optimization.data import load_sndlib_native
from telecom_network_optimization.mir import mir_function, enumerate_mir_cutset_rows
from telecom_network_optimization.heuristic import run_greedy


def test_parse_official_example():
    data = load_sndlib_native(ROOT / "data/examples/network.txt")
    assert len(data.nodes) == 5
    assert len(data.links) == 8
    assert len(data.demands) == 3
    assert {d.volume for d in data.demands} == {27, 50, 126}
    assert any(link.base_capacity == 63 for link in data.links)


def test_mir_function_basic_properties():
    assert mir_function(63, 127, 63) == 1
    assert mir_function(252, 127, 63) == 4
    assert mir_function(63, 63, 63) == 63


def test_cutset_rows_generated():
    data = load_sndlib_native(ROOT / "data/examples/network.txt")
    rows = enumerate_mir_cutset_rows(data)
    assert rows
    assert all(row["rhs"] > 0 for row in rows)
    assert all(row["coefficients"] for row in rows)


def test_greedy_produces_feasible_routing():
    data = load_sndlib_native(ROOT / "data/examples/network.txt")
    result = run_greedy(data)
    assert result.feasible
    assert result.objective is not None
    assert set(result.routes) == {d.id for d in data.demands}
