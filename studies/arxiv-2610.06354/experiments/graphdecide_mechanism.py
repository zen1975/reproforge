"""Independent lightweight reconstruction of GraphDecide's evaluator contract."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import inf
from typing import Callable, Iterable, Mapping, Sequence


def _edge(u: str, v: str) -> tuple[str, str]:
    if u == v:
        raise ValueError("self loops are outside this synthetic simple-graph contract")
    return tuple(sorted((u, v)))


@dataclass(frozen=True)
class SimpleGraph:
    vertices: tuple[str, ...]
    edges: frozenset[tuple[str, str]]

    @classmethod
    def build(cls, vertices: Iterable[str], edges: Iterable[tuple[str, str]]) -> "SimpleGraph":
        vertices_tuple = tuple(vertices)
        vertex_set = set(vertices_tuple)
        if len(vertex_set) != len(vertices_tuple):
            raise ValueError("vertices must be unique")
        normalized = frozenset(_edge(u, v) for u, v in edges)
        if any(u not in vertex_set or v not in vertex_set for u, v in normalized):
            raise ValueError("edge endpoint missing from vertex set")
        return cls(vertices_tuple, normalized)

    def neighbors(self, vertex: str, removed: str | None = None) -> tuple[str, ...]:
        if vertex not in self.vertices or vertex == removed:
            raise ValueError("unknown or removed vertex")
        values: list[str] = []
        for u, v in self.edges:
            if removed in (u, v):
                continue
            if u == vertex:
                values.append(v)
            elif v == vertex:
                values.append(u)
        return tuple(sorted(values))

    def adjacent(self, u: str, v: str) -> bool:
        return _edge(u, v) in self.edges

    def degree(self, vertex: str) -> int:
        return len(self.neighbors(vertex))

    def component_count(self, removed: str | None = None) -> int:
        remaining = [v for v in self.vertices if v != removed]
        unseen = set(remaining)
        count = 0
        while unseen:
            count += 1
            start = min(unseen)
            queue = deque([start])
            unseen.remove(start)
            while queue:
                current = queue.popleft()
                for nxt in self.neighbors(current, removed=removed):
                    if nxt in unseen:
                        unseen.remove(nxt)
                        queue.append(nxt)
        return count

    def connected(self) -> bool:
        return self.component_count() <= 1

    def has_cycle(self) -> bool:
        visited: set[str] = set()

        def dfs(node: str, parent: str | None) -> bool:
            visited.add(node)
            for nxt in self.neighbors(node):
                if nxt == parent:
                    continue
                if nxt in visited or dfs(nxt, node):
                    return True
            return False

        return any(v not in visited and dfs(v, None) for v in self.vertices)

    def shortest_distance(self, source: str, target: str) -> int | None:
        if source == target:
            return 0
        seen = {source}
        queue = deque([(source, 0)])
        while queue:
            node, distance = queue.popleft()
            for nxt in self.neighbors(node):
                if nxt == target:
                    return distance + 1
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, distance + 1))
        return None

    def is_articulation(self, vertex: str) -> bool:
        if vertex not in self.vertices:
            raise ValueError("unknown vertex")
        return self.component_count(removed=vertex) > self.component_count()


@dataclass(frozen=True)
class Query:
    task: str
    args: Mapping[str, object]
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class QueryResult:
    choice: str | None
    reference: str
    supported: bool
    valid: bool
    correct: bool


def reference_answer(graph: SimpleGraph, query: Query) -> str:
    args = query.args
    if query.task == "adjacency":
        return "yes" if graph.adjacent(str(args["u"]), str(args["v"])) else "no"
    if query.task == "degree":
        return str(graph.degree(str(args["vertex"])))
    if query.task == "cycle":
        return "yes" if graph.has_cycle() else "no"
    if query.task == "connectivity":
        return "yes" if graph.connected() else "no"
    if query.task == "distance_leq":
        distance = graph.shortest_distance(str(args["source"]), str(args["target"]))
        threshold = int(args["threshold"])
        return "yes" if distance is not None and distance <= threshold else "no"
    if query.task == "articulation":
        return "yes" if graph.is_articulation(str(args["vertex"])) else "no"
    raise ValueError(f"unsupported task: {query.task}")


def evaluate_query(graph: SimpleGraph, query: Query, choice: str | None) -> QueryResult:
    reference = reference_answer(graph, query)
    supported = choice is not None
    valid = supported and choice in query.candidates
    return QueryResult(
        choice=choice,
        reference=reference,
        supported=supported,
        valid=valid,
        correct=bool(valid and choice == reference),
    )


@dataclass(frozen=True)
class TSPInstance:
    cities: tuple[str, ...]
    distances: Mapping[tuple[str, str], float]
    reference: float

    def distance(self, u: str, v: str) -> float:
        if u == v:
            return 0.0
        key = tuple(sorted((u, v)))
        if key not in self.distances:
            raise ValueError(f"missing distance: {u}-{v}")
        return float(self.distances[key])


@dataclass(frozen=True)
class TrajectoryResult:
    status: str
    route: tuple[str, ...]
    calls: int
    complete: bool
    legal: bool
    objective: float | None
    gap: float | None
    candidate_history: tuple[tuple[str, ...], ...]


Policy = Callable[[Mapping[str, object], tuple[str, ...]], str | None]


def run_tsp(instance: TSPInstance, policy: Policy, start: str) -> TrajectoryResult:
    if start not in instance.cities:
        raise ValueError("start must be a city")
    route = [start]
    unvisited = set(instance.cities) - {start}
    history: list[tuple[str, ...]] = []
    calls = 0

    while unvisited:
        candidates = tuple(sorted(unvisited))
        history.append(candidates)
        state = {
            "start": start,
            "current": route[-1],
            "route": tuple(route),
            "unvisited": candidates,
        }
        choice = policy(state, candidates)
        calls += 1
        if choice is None:
            return TrajectoryResult(
                "unsupported", tuple(route), calls, False, False, None, None, tuple(history)
            )
        if choice not in candidates:
            return TrajectoryResult(
                "invalid_action", tuple(route), calls, False, False, None, None, tuple(history)
            )
        route.append(choice)
        unvisited.remove(choice)

    closed_route = tuple(route + [start])
    length = sum(instance.distance(u, v) for u, v in zip(closed_route, closed_route[1:]))
    gap = 100.0 * (length - instance.reference) / instance.reference
    return TrajectoryResult(
        "complete",
        closed_route,
        calls,
        True,
        True,
        length,
        gap,
        tuple(history),
    )


def summarize_trajectories(rows: Sequence[TrajectoryResult]) -> dict[str, float | int | None]:
    n = len(rows)
    completed = [row for row in rows if row.complete and row.legal]
    return {
        "scheduled": n,
        "completed": len(completed),
        "coverage": len(completed) / n if n else 0.0,
        "mean_gap": (
            sum(float(row.gap) for row in completed if row.gap is not None) / len(completed)
            if completed
            else None
        ),
        "failed": n - len(completed),
    }
