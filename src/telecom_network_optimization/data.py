"""Data structures and a parser for the SNDlib native ASCII format.

The parser supports the nodes, links, and demands required by this prototype.
It intentionally ignores admissible paths and hop limits because the paper's
core experiments allow all paths and do not impose hop limits.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import math
import re


_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_NAME = r"[A-Za-z0-9_.-]+"


@dataclass(frozen=True)
class Module:
    capacity: int
    cost: float


@dataclass(frozen=True)
class Link:
    id: str
    u: str
    v: str
    base_capacity: int
    base_capacity_cost: float
    routing_cost: float
    fixed_charge_cost: float
    modules: tuple[Module, ...]


@dataclass(frozen=True)
class Demand:
    id: str
    source: str
    target: str
    volume: int


@dataclass(frozen=True)
class NetworkData:
    name: str
    nodes: tuple[str, ...]
    links: tuple[Link, ...]
    demands: tuple[Demand, ...]
    source: str = "SNDlib"

    def scaled(self, factor: float) -> "NetworkData":
        """Return a scenario with demand volumes multiplied by ``factor``.

        Rounded to the nearest integer because SNDlib traffic units and the
        paper's demands are integral in the tested instances.
        """
        if factor <= 0:
            raise ValueError("Demand scale must be positive.")
        return replace(
            self,
            name=f"{self.name}_scale_{factor:g}",
            demands=tuple(
                replace(d, volume=max(1, int(round(d.volume * factor))))
                for d in self.demands
            ),
        )


def _strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def _section(text: str, begin: str, end: str) -> str:
    try:
        start = re.search(rf"\b{begin}\s*\(", text, flags=re.IGNORECASE)
        if start is None:
            raise ValueError(f"Missing {begin} section.")
        finish = re.search(rf"\b{end}\s*\(", text[start.end():], flags=re.IGNORECASE)
        if finish is None:
            raise ValueError(f"Missing {end} section after {begin}.")
        return text[start.end(): start.end() + finish.start()]
    except re.error as exc:
        raise ValueError(f"Unable to parse {begin} section: {exc}") from exc


def load_sndlib_native(path: str | Path) -> NetworkData:
    """Parse a SNDlib native-format network file.

    Supported fields: node names, undirected links, preinstalled capacities,
    per-unit routing costs, module capacities/costs, and point-to-point demands.
    Fixed-charge costs, coordinates, hop limits and admissible-path lists are
    read only as context and are not included in the model.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = _strip_comments(raw)

    node_body = _section(text, "NODES", "LINKS")
    link_body = _section(text, "LINKS", "DEMANDS")
    demand_start = re.search(r"\bDEMANDS\s*\(", text, flags=re.IGNORECASE)
    if demand_start is None:
        raise ValueError("Missing DEMANDS section.")
    after_demands = text[demand_start.end():]
    admissible = re.search(r"\bADMISSIBLE_PATHS\s*\(", after_demands, flags=re.IGNORECASE)
    demand_body = after_demands[:admissible.start()] if admissible else after_demands

    node_pattern = re.compile(rf"({_NAME})\s*\(\s*{_NUMBER}\s+{_NUMBER}\s*\)")
    nodes = tuple(dict.fromkeys(m.group(1) for m in node_pattern.finditer(node_body)))
    if len(nodes) < 2:
        raise ValueError(f"Could not parse at least two nodes from {path}.")

    link_pattern = re.compile(
        rf"({_NAME})\s*\(\s*({_NAME})\s+({_NAME})\s*\)\s*"
        rf"({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})\s+({_NUMBER})\s*"
        rf"\(\s*([^()]*)\s*\)"
    )
    links: list[Link] = []
    for match in link_pattern.finditer(link_body):
        link_id, u, v = match.group(1), match.group(2), match.group(3)
        base_cap = float(match.group(4))
        base_cost = float(match.group(5))
        routing_cost = float(match.group(6))
        fixed_cost = float(match.group(7))
        module_values = re.findall(_NUMBER, match.group(8))
        if len(module_values) % 2:
            raise ValueError(f"Malformed module capacity/cost list on link {link_id}.")
        modules = tuple(
            Module(int(round(float(module_values[i]))), float(module_values[i + 1]))
            for i in range(0, len(module_values), 2)
        )
        if not modules:
            raise ValueError(f"Link {link_id} has no installable modules.")
        if u not in nodes or v not in nodes:
            raise ValueError(f"Link {link_id} references an unknown node.")
        links.append(Link(link_id, u, v, int(round(base_cap)), base_cost,
                          routing_cost, fixed_cost, modules))
    if not links:
        raise ValueError(f"Could not parse links from {path}.")

    demand_pattern = re.compile(
        rf"({_NAME})\s*\(\s*({_NAME})\s+({_NAME})\s*\)\s*"
        rf"({_NUMBER})\s+({_NUMBER})\s+({_NAME})\s*\(\s*([^()]*)\s*\)"
    )
    demands: list[Demand] = []
    for match in demand_pattern.finditer(demand_body):
        demand_id, source, target = match.group(1), match.group(2), match.group(3)
        unit = float(match.group(4))
        quantity = float(match.group(5))
        volume = int(round(unit * quantity))
        if source not in nodes or target not in nodes:
            raise ValueError(f"Demand {demand_id} references an unknown node.")
        if source == target:
            raise ValueError(f"Demand {demand_id} has identical source/target nodes.")
        if volume <= 0:
            raise ValueError(f"Demand {demand_id} must have positive volume.")
        demands.append(Demand(demand_id, source, target, volume))
    if not demands:
        raise ValueError(f"Could not parse demands from {path}.")

    return NetworkData(path.stem, nodes, tuple(links), tuple(demands),
                       source="SNDlib native-format example/archive")
