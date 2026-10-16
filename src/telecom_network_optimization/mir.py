"""MIR coefficient function and exhaustive cutset-inequality generation."""
from __future__ import annotations

from itertools import combinations
import math
from typing import Iterable

from .data import NetworkData


def _remainder(a: int, c: int) -> int:
    """Paper's remainder r_(a,c), with values in {1,...,c} for a > 0."""
    if a <= 0 or c <= 0:
        raise ValueError("MIR remainder expects positive a and c.")
    return a - c * (math.ceil(a / c) - 1)


def mir_function(a: int, d: int, c: int) -> int:
    """Compute F_(d,c)(a) from Eq. (5) for positive integer inputs."""
    if a <= 0 or d <= 0 or c <= 0:
        raise ValueError("MIR function expects positive integer inputs.")
    r_dc = _remainder(d, c)
    r_ac = _remainder(a, c)
    return int(math.ceil(a / c) * r_dc - max(r_dc - r_ac, 0))


def unique_capacity_types(data: NetworkData) -> tuple[int, ...]:
    return tuple(sorted({module.capacity for link in data.links for module in link.modules}))


def unique_undirected_cuts(nodes: Iterable[str]) -> list[frozenset[str]]:
    """Enumerate each nontrivial undirected cut once; practical for small n only."""
    ordered = tuple(nodes)
    if len(ordered) > 18:
        raise ValueError(
            "Exhaustive cut enumeration is intended for small instances (<=18 nodes)."
        )
    if len(ordered) < 2:
        return []
    first, rest = ordered[0], ordered[1:]
    cuts: list[frozenset[str]] = []
    for r in range(len(rest) + 1):
        for subset in combinations(rest, r):
            side = frozenset((first, *subset))
            if len(side) < len(ordered):
                cuts.append(side)
    return cuts


def enumerate_mir_cutset_rows(data: NetworkData) -> list[dict]:
    """Return MIR cutset inequalities for all undirected cuts.

    The cut demand is the total OD traffic with terminals on opposite sides.
    Preinstalled capacity crossing the cut is subtracted first; remaining
    capacity must be purchased through integer modules.
    """
    rows: list[dict] = []
    nodes = set(data.nodes)
    for side in unique_undirected_cuts(data.nodes):
        cross = [link for link in data.links if (link.u in side) != (link.v in side)]
        if not cross:
            continue
        crossing_demand = sum(
            demand.volume for demand in data.demands
            if (demand.source in side) != (demand.target in side)
        )
        preinstalled = sum(link.base_capacity for link in cross)
        residual = max(0, crossing_demand - preinstalled)
        if residual == 0:
            continue
        for reference_capacity in unique_capacity_types(data):
            rhs = mir_function(residual, residual, reference_capacity)
            coeffs: list[tuple[str, int, int]] = []
            for link in cross:
                for module_idx, module in enumerate(link.modules):
                    coeff = mir_function(module.capacity, residual, reference_capacity)
                    if coeff:
                        coeffs.append((link.id, module_idx, coeff))
            if coeffs and rhs > 0:
                rows.append({
                    "side": sorted(side),
                    "crossing_links": [link.id for link in cross],
                    "crossing_demand": crossing_demand,
                    "preinstalled_capacity": preinstalled,
                    "residual_demand": residual,
                    "reference_capacity": reference_capacity,
                    "coefficients": coeffs,
                    "rhs": rhs,
                })
    return rows
