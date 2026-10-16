"""CLI for reproducible baseline/cut/heuristic experiments."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from telecom_network_optimization.data import load_sndlib_native
from telecom_network_optimization.heuristic import run_greedy
from telecom_network_optimization.model import solve_milp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", default=str(ROOT / "data/examples/network.txt"),
                        help="Path to a SNDlib native-format network file")
    parser.add_argument("--scales", nargs="+", type=float, default=[1.0, 2.0, 3.0],
                        help="Demand scale factors for stress tests (default: 1 2 3)")
    parser.add_argument("--time-limit", type=float, default=60.0,
                        help="Per-MILP time limit in seconds (default: 60)")
    parser.add_argument("--capacity-mode", choices=["modular", "explicit"], default="modular")
    parser.add_argument("--output", default=str(ROOT / "experiments/results/summary.csv"),
                        help="CSV path for the experiment summary")
    parser.add_argument("--routes-output", default=str(ROOT / "experiments/results/heuristic_routes.json"),
                        help="JSON path for heuristic route details")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    instance_path = Path(args.instance)
    if not instance_path.exists():
        print(f"ERROR: instance does not exist: {instance_path}", file=sys.stderr)
        return 2
    try:
        base_data = load_sndlib_native(instance_path)
    except Exception as exc:
        print(f"ERROR parsing SNDlib instance: {exc}", file=sys.stderr)
        return 2

    rows: list[dict] = []
    route_details: dict = {}
    for scale in args.scales:
        data = base_data.scaled(scale)
        print(f"\nInstance={data.name} | nodes={len(data.nodes)} | links={len(data.links)} | demands={len(data.demands)}")
        methods = []
        for with_cuts in (False, True):
            try:
                result, _ = solve_milp(data, capacity_mode=args.capacity_mode,
                                       add_mir_cuts=with_cuts, time_limit=args.time_limit)
            except RuntimeError as exc:
                print(f"Solver unavailable: {exc}")
                return 3
            methods.append(result)
            print(f"{result.method}: status={result.status}, objective={result.objective}, runtime={result.runtime_sec:.4f}s, cuts={result.cuts_added}")
            rows.append({
                "instance": instance_path.name,
                "demand_scale": scale,
                "method": result.method,
                "capacity_mode": args.capacity_mode,
                "status": result.status,
                "objective": result.objective,
                "runtime_sec": round(result.runtime_sec, 6),
                "lower_bound": result.lower_bound,
                "upper_bound": result.upper_bound,
                "mip_gap_pct": result.mip_gap_pct,
                "cuts_added": result.cuts_added,
                "feasible": result.objective is not None,
                "message": result.message,
            })

        try:
            heuristic = run_greedy(data)
        except Exception as exc:
            print(f"Heuristic failed: {type(exc).__name__}: {exc}")
            return 4
        opt_reference = None
        for result in methods:
            if result.objective is not None and "optimal" in result.status.lower():
                opt_reference = result.objective if opt_reference is None else min(opt_reference, result.objective)
        gap_vs_opt = None
        if heuristic.feasible and opt_reference is not None and abs(opt_reference) > 1e-12:
            gap_vs_opt = max(0.0, (heuristic.objective - opt_reference) / abs(opt_reference) * 100.0)
        print(f"Greedy heuristic: status={heuristic.status}, objective={heuristic.objective}, runtime={heuristic.runtime_sec:.4f}s, gap_vs_proven_optimum={gap_vs_opt}")
        rows.append({
            "instance": instance_path.name,
            "demand_scale": scale,
            "method": "Greedy single-path heuristic",
            "capacity_mode": args.capacity_mode,
            "status": heuristic.status,
            "objective": heuristic.objective,
            "runtime_sec": round(heuristic.runtime_sec, 6),
            "lower_bound": None,
            "upper_bound": None,
            "mip_gap_pct": None,
            "cuts_added": 0,
            "feasible": heuristic.feasible,
            "message": f"gap_vs_proven_optimum_pct={gap_vs_opt}",
        })
        route_details[data.name] = {
            "objective": heuristic.objective,
            "routing_cost": heuristic.routing_cost,
            "module_cost": heuristic.module_cost,
            "feasible": heuristic.feasible,
            "routes": heuristic.routes,
            "edge_loads": heuristic.edge_loads,
            "module_counts": {f"{e}::module_{m}": c for (e, m), c in heuristic.module_counts.items()},
        }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["instance", "demand_scale", "method", "capacity_mode", "status", "objective",
              "runtime_sec", "lower_bound", "upper_bound", "mip_gap_pct", "cuts_added", "feasible", "message"]
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    route_output = Path(args.routes_output)
    route_output.parent.mkdir(parents=True, exist_ok=True)
    route_output.write_text(json.dumps(route_details, indent=2), encoding="utf-8")
    print(f"\nWrote experiment summary: {output}")
    print(f"Wrote heuristic route details: {route_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
