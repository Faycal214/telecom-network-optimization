"""Pyomo MILP for an undirected capacitated multicommodity network design."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

from .data import NetworkData
from .mir import enumerate_mir_cutset_rows


@dataclass
class SolveResult:
    method: str
    status: str
    runtime_sec: float
    objective: float | None
    lower_bound: float | None
    upper_bound: float | None
    mip_gap_pct: float | None
    cuts_added: int = 0
    message: str = ""


def build_model(data: NetworkData, capacity_mode: str = "modular", add_mir_cuts: bool = False):
    """Build the base MILP, optionally strengthened by MIR cutset inequalities.

    Model assumptions: undirected links with shared capacity in both directions;
    continuous multicommodity flow; integer module counts in modular mode;
    no fixed-charge cost; preinstalled capacity is available and its historic
    cost is treated as sunk; no hop limits or admissible-path restrictions.
    """
    try:
        import pyomo.environ as pyo
    except ImportError as exc:
        raise RuntimeError("Pyomo is not installed. Run `pip install -e .`.") from exc

    if capacity_mode not in {"modular", "explicit"}:
        raise ValueError("capacity_mode must be 'modular' or 'explicit'.")

    link_by_id = {link.id: link for link in data.links}
    demand_by_id = {d.id: d for d in data.demands}
    arcs: list[tuple[str, str, str]] = []
    arc_ids_by_link: dict[str, list[int]] = {link.id: [] for link in data.links}
    outgoing: dict[str, list[int]] = {node: [] for node in data.nodes}
    incoming: dict[str, list[int]] = {node: [] for node in data.nodes}
    for link in data.links:
        for tail, head in ((link.u, link.v), (link.v, link.u)):
            arc_id = len(arcs)
            arcs.append((link.id, tail, head))
            arc_ids_by_link[link.id].append(arc_id)
            outgoing[tail].append(arc_id)
            incoming[head].append(arc_id)

    edge_modules = [(link.id, idx) for link in data.links for idx, _ in enumerate(link.modules)]
    module_lookup = {(link.id, idx): module for link in data.links for idx, module in enumerate(link.modules)}
    model = pyo.ConcreteModel(name=f"Capacitated network design: {data.name}")
    model.N = pyo.Set(initialize=list(data.nodes), ordered=True)
    model.E = pyo.Set(initialize=[link.id for link in data.links], ordered=True)
    model.D = pyo.Set(initialize=[d.id for d in data.demands], ordered=True)
    model.A = pyo.Set(initialize=list(range(len(arcs))), ordered=True)
    model.EM = pyo.Set(dimen=2, initialize=edge_modules, ordered=True)
    var_domain = pyo.NonNegativeIntegers if capacity_mode == "modular" else pyo.Binary
    model.flow = pyo.Var(model.D, model.A, domain=pyo.NonNegativeReals)
    model.x = pyo.Var(model.EM, domain=var_domain)

    @model.Constraint(model.D, model.N)
    def flow_balance(m, d_id, node):
        demand = demand_by_id[d_id]
        rhs = demand.volume if node == demand.source else (-demand.volume if node == demand.target else 0)
        return sum(m.flow[d_id, a] for a in outgoing[node]) - sum(
            m.flow[d_id, a] for a in incoming[node]
        ) == rhs

    @model.Constraint(model.E)
    def link_capacity(m, edge_id):
        link = link_by_id[edge_id]
        total_flow = sum(m.flow[d_id, a] for d_id in demand_by_id for a in arc_ids_by_link[edge_id])
        added_capacity = sum(
            module_lookup[(edge_id, module_idx)].capacity * m.x[edge_id, module_idx]
            for module_idx in range(len(link.modules))
        )
        return total_flow <= link.base_capacity + added_capacity

    if capacity_mode == "explicit":
        @model.Constraint(model.E)
        def at_most_one_module(m, edge_id):
            link = link_by_id[edge_id]
            return sum(m.x[edge_id, idx] for idx in range(len(link.modules))) <= 1

    def objective_rule(m):
        routing_cost = sum(
            link_by_id[edge_id].routing_cost * m.flow[d_id, a]
            for edge_id, arc_ids in arc_ids_by_link.items()
            for d_id in demand_by_id
            for a in arc_ids
        )
        module_cost = sum(module_lookup[(edge_id, idx)].cost * m.x[edge_id, idx]
                          for edge_id, idx in edge_modules)
        return routing_cost + module_cost
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    cuts_added = 0
    if add_mir_cuts:
        rows = enumerate_mir_cutset_rows(data)
        model.mir_cuts = pyo.ConstraintList()
        for row in rows:
            lhs = sum(coeff * model.x[edge_id, module_idx]
                      for edge_id, module_idx, coeff in row["coefficients"])
            model.mir_cuts.add(lhs >= row["rhs"])
        cuts_added = len(rows)

    model._telecom_metadata = {
        "data": data,
        "link_by_id": link_by_id,
        "demand_by_id": demand_by_id,
        "arcs": arcs,
        "arc_ids_by_link": arc_ids_by_link,
        "edge_modules": edge_modules,
        "module_lookup": module_lookup,
        "cuts_added": cuts_added,
        "capacity_mode": capacity_mode,
    }
    return model


def _bound_value(results: Any, attribute: str) -> float | None:
    problem = getattr(results, "problem", None)
    candidates = []
    if problem is not None:
        candidates.append(problem)
        try:
            candidates.extend(list(problem))
        except TypeError:
            pass
    for item in candidates:
        value = getattr(item, attribute, None)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def solve_milp(data: NetworkData, capacity_mode: str = "modular",
               add_mir_cuts: bool = False, time_limit: float = 60.0) -> tuple[SolveResult, Any | None]:
    """Solve with Pyomo + HiGHS and return a result plus the model if available."""
    try:
        import pyomo.environ as pyo
    except ImportError as exc:
        raise RuntimeError("Pyomo is not installed. Run `pip install -e .`.") from exc

    model = build_model(data, capacity_mode=capacity_mode, add_mir_cuts=add_mir_cuts)
    solver = pyo.SolverFactory("appsi_highs")
    if solver is None or not solver.available(exception_flag=False):
        raise RuntimeError("HiGHS is unavailable. Install it with `pip install highspy`.")
    try:
        solver.options["time_limit"] = float(time_limit)
    except Exception:
        pass

    start = time.perf_counter()
    try:
        results = solver.solve(model, tee=False)
        runtime = time.perf_counter() - start
        termination = str(results.solver.termination_condition)
        status = str(results.solver.status)
        objective = None
        try:
            if model.total_cost.expr is not None:
                objective = float(pyo.value(model.total_cost))
        except (ValueError, RuntimeError):
            objective = None
        lb = _bound_value(results, "lower_bound")
        ub = _bound_value(results, "upper_bound")
        if "optimal" in termination.lower() and objective is not None:
            lb = objective
            ub = objective
        elif ub is None and objective is not None:
            ub = objective
        gap = None
        if lb is not None and ub is not None and abs(lb) > 1e-12:
            gap = max(0.0, (ub - lb) / abs(lb) * 100.0)
        answer = SolveResult(
            method="MILP + MIR cutset inequalities" if add_mir_cuts else "Base MILP",
            status=termination,
            runtime_sec=runtime,
            objective=objective,
            lower_bound=lb,
            upper_bound=ub,
            mip_gap_pct=gap,
            cuts_added=model._telecom_metadata["cuts_added"],
            message=f"solver_status={status}",
        )
        return answer, model
    except Exception as exc:
        runtime = time.perf_counter() - start
        return SolveResult(
            method="MILP + MIR cutset inequalities" if add_mir_cuts else "Base MILP",
            status="error", runtime_sec=runtime, objective=None,
            lower_bound=None, upper_bound=None, mip_gap_pct=None,
            cuts_added=model._telecom_metadata["cuts_added"],
            message=f"{type(exc).__name__}: {exc}",
        ), model
