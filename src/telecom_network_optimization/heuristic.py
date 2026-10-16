"""Deterministic path-based greedy heuristic for capacitated network design."""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Iterable

import networkx as nx

from .data import Link, NetworkData


@dataclass
class HeuristicResult:
    status: str
    runtime_sec: float
    objective: float | None
    routing_cost: float | None
    module_cost: float | None
    feasible: bool
    routes: dict[str, list[str]]
    edge_loads: dict[str, float]
    module_counts: dict[tuple[str, int], int]
    message: str = ""


def minimum_module_plan(required_capacity: int, link: Link) -> tuple[float, tuple[int, ...]]:
    """Find a minimum-cost capacity cover for one link.

    Exact enumeration for the two-module-type instances in the starter data;
    a dynamic program is used for modest more-general instances. Very large
    targets with >2 module types use a cost-per-capacity greedy fallback.
    """
    if required_capacity <= 0:
        return 0.0, tuple(0 for _ in link.modules)
    modules = list(link.modules)
    if not modules:
        raise ValueError(f"Link {link.id} has no installable modules.")
    if len(modules) == 1:
        count = math.ceil(required_capacity / modules[0].capacity)
        return count * modules[0].cost, (count,)
    if len(modules) == 2:
        small_idx = min(range(2), key=lambda i: modules[i].capacity)
        large_idx = 1 - small_idx
        small, large = modules[small_idx], modules[large_idx]
        best_cost = math.inf
        best_counts = (0, 0)
        max_large = math.ceil(required_capacity / large.capacity)
        for n_large in range(max_large + 1):
            residual = max(0, required_capacity - n_large * large.capacity)
            n_small = math.ceil(residual / small.capacity)
            counts = [0, 0]
            counts[small_idx] = n_small
            counts[large_idx] = n_large
            cost = n_small * small.cost + n_large * large.cost
            if cost < best_cost:
                best_cost, best_counts = cost, tuple(counts)
        return best_cost, best_counts

    max_module = max(m.capacity for m in modules)
    if required_capacity <= 100_000:
        limit = required_capacity + max_module
        inf = float("inf")
        dp = [inf] * (limit + 1)
        parent: list[tuple[int, int] | None] = [None] * (limit + 1)
        dp[0] = 0.0
        for cap in range(limit + 1):
            if not math.isfinite(dp[cap]):
                continue
            for idx, module in enumerate(modules):
                nxt = cap + module.capacity
                if nxt <= limit and dp[cap] + module.cost < dp[nxt]:
                    dp[nxt] = dp[cap] + module.cost
                    parent[nxt] = (cap, idx)
        target = min(range(required_capacity, limit + 1), key=lambda cap: dp[cap])
        counts = [0] * len(modules)
        cap = target
        while cap > 0 and parent[cap] is not None:
            prev, idx = parent[cap]
            counts[idx] += 1
            cap = prev
        return dp[target], tuple(counts)

    idx = min(range(len(modules)), key=lambda i: modules[i].cost / modules[i].capacity)
    count = math.ceil(required_capacity / modules[idx].capacity)
    counts = [0] * len(modules)
    counts[idx] = count
    return count * modules[idx].cost, tuple(counts)


def run_greedy(data: NetworkData, k_paths: int = 30) -> HeuristicResult:
    """Route larger demands first, choosing the path with least incremental cost.

    The heuristic routes each OD demand unsplittably on one path, then provisions
    integer modules to cover the aggregate load. It is feasible by construction
    when every source-target pair is connected, but is not guaranteed optimal.
    """
    start = time.perf_counter()
    graph = nx.Graph()
    graph.add_nodes_from(data.nodes)
    link_by_id = {link.id: link for link in data.links}
    edge_key_to_id = {}
    loads = {link.id: 0.0 for link in data.links}
    routes: dict[str, list[str]] = {}

    for link in data.links:
        graph.add_edge(link.u, link.v, link_id=link.id, weight=link.routing_cost)
        edge_key_to_id[frozenset((link.u, link.v))] = link.id

    demands = sorted(data.demands, key=lambda d: (-d.volume, d.id))
    try:
        for demand in demands:
            q = demand.volume
            # Score edges by routing expense plus the module cost increase caused
            # by assigning this demand to that link.
            edge_weights: dict[str, float] = {}
            for link in data.links:
                old_need = max(0, int(round(loads[link.id])) - link.base_capacity)
                new_need = max(0, int(round(loads[link.id] + q)) - link.base_capacity)
                old_cost = minimum_module_plan(old_need, link)[0]
                new_cost = minimum_module_plan(new_need, link)[0]
                edge_weights[link.id] = link.routing_cost * q + new_cost - old_cost
                graph[link.u][link.v]["weight"] = edge_weights[link.id]

            path_gen = nx.shortest_simple_paths(graph, demand.source, demand.target, weight="weight")
            best_path = None
            best_score = math.inf
            for path_no, path in enumerate(path_gen):
                if path_no >= k_paths:
                    break
                edge_ids = [edge_key_to_id[frozenset((u, v))] for u, v in zip(path, path[1:])]
                score = sum(edge_weights[eid] for eid in edge_ids)
                if score < best_score:
                    best_score, best_path = score, path
            if best_path is None:
                raise nx.NetworkXNoPath(f"No path for demand {demand.id}.")
            routes[demand.id] = list(best_path)
            for u, v in zip(best_path, best_path[1:]):
                edge_id = edge_key_to_id[frozenset((u, v))]
                loads[edge_id] += q
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        return HeuristicResult("infeasible", time.perf_counter() - start, None, None, None,
                               False, routes, loads, {}, str(exc))

    module_counts: dict[tuple[str, int], int] = {}
    module_cost = 0.0
    routing_cost = 0.0
    feasible = True
    for link in data.links:
        routing_cost += link.routing_cost * loads[link.id]
        required = max(0, int(round(loads[link.id])) - link.base_capacity)
        cost, counts = minimum_module_plan(required, link)
        module_cost += cost
        installed_capacity = link.base_capacity + sum(
            module.capacity * counts[idx] for idx, module in enumerate(link.modules)
        )
        feasible = feasible and installed_capacity + 1e-9 >= loads[link.id]
        for idx, count in enumerate(counts):
            if count:
                module_counts[(link.id, idx)] = count
    return HeuristicResult(
        status="feasible" if feasible else "infeasible",
        runtime_sec=time.perf_counter() - start,
        objective=routing_cost + module_cost,
        routing_cost=routing_cost,
        module_cost=module_cost,
        feasible=feasible,
        routes=routes,
        edge_loads=loads,
        module_counts=module_counts,
    )
