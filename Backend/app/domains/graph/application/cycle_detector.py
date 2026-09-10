   
from __future__ import annotations

import uuid
from collections import defaultdict, deque

from app.domains.graph.domain.entities import TaskDependency


class CycleDetector:
       

    def would_create_cycle(
        self,
        existing: list[TaskDependency],
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
    ) -> bool:
           
                                                  
        graph: dict[str, set[str]] = defaultdict(set)
        for dep in existing:
            graph[str(dep.upstream_id)].add(str(dep.downstream_id))

                                      
        graph[str(upstream_id)].add(str(downstream_id))

        return self._has_cycle(graph)

    def would_create_cycle_in_graph(
        self,
        graph: dict[str, set[str]],
        upstream: str,
        downstream: str,
    ) -> bool:
           
                                                        
                                                              
        return self._can_reach(graph, start=downstream, target=upstream)

    def find_cycle_path(
        self,
        existing: list[TaskDependency],
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
    ) -> list[str]:
           
        graph: dict[str, set[str]] = defaultdict(set)
        for dep in existing:
            graph[str(dep.upstream_id)].add(str(dep.downstream_id))
        graph[str(upstream_id)].add(str(downstream_id))

        if not self._has_cycle(graph):
            return []

        return self._trace_cycle(graph, str(upstream_id))

    def validate_bulk_edges(
        self,
        existing: list[TaskDependency],
        new_edges: list[tuple[str, str]],
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
           
                                                           
        graph: dict[str, set[str]] = defaultdict(set)
        for dep in existing:
            graph[str(dep.upstream_id)].add(str(dep.downstream_id))

        safe: list[tuple[str, str]] = []
        rejected: list[tuple[str, str]] = []

        for upstream, downstream in new_edges:
            if upstream == downstream:
                rejected.append((upstream, downstream))
                continue

            if self.would_create_cycle_in_graph(graph, upstream, downstream):
                rejected.append((upstream, downstream))
            else:
                                                                      
                graph[upstream].add(downstream)
                safe.append((upstream, downstream))

        return safe, rejected

                                                                    

    @staticmethod
    def _has_cycle(graph: dict[str, set[str]]) -> bool:
           
        all_nodes: set[str] = set()
        in_degree: dict[str, int] = defaultdict(int)

        for node, neighbors in graph.items():
            all_nodes.add(node)
            for neighbor in neighbors:
                in_degree[neighbor] += 1
                all_nodes.add(neighbor)

                                                      
        queue: deque[str] = deque(
            node for node in all_nodes if in_degree.get(node, 0) == 0
        )
        processed = 0

        while queue:
            node = queue.popleft()
            processed += 1
            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return processed != len(all_nodes)

    @staticmethod
    def _can_reach(
        graph: dict[str, set[str]], start: str, target: str
    ) -> bool:
           
        if start == target:
            return True

        visited: set[str] = set()
        queue: deque[str] = deque([start])

        while queue:
            node = queue.popleft()
            if node == target:
                return True
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, set()):
                queue.append(neighbor)

        return False

    @staticmethod
    def _trace_cycle(graph: dict[str, set[str]], start: str) -> list[str]:
           
        visited: set[str] = set()
        path: list[str] = []
        path_set: set[str] = set()

        def dfs(node: str) -> bool:
            if node in path_set:
                                                              
                cycle_start = path.index(node)
                path[cycle_start:] = path[cycle_start:] + [node]
                return True
            if node in visited:
                return False

            visited.add(node)
            path.append(node)
            path_set.add(node)

            for neighbor in graph.get(node, set()):
                if dfs(neighbor):
                    return True

            path.pop()
            path_set.discard(node)
            return False

        dfs(start)
        return path if len(path) > 1 and path[0] == path[-1] else []
