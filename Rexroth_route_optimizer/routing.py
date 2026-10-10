from abc import ABC, abstractmethod
from collections import deque

from models import RouteResult


class IRoutingEngine(ABC):

    @abstractmethod
    def CalculateRoute(self, start, destinations):
        pass


class RoutingEngine(IRoutingEngine):

    def __init__(self, topology):
        self.topology = topology

    def CalculateRoute(self, start, destinations):
        if not destinations:
            raise ValueError("no destinations were provided.")

        if self.topology.IsBlocked(start):
            raise ValueError("starting location is blocked.")

        remaining = list(destinations)
        current = start
        route = [start]
        total_distance = 0

        while remaining:
            paths = {
                destination: self._find_path(
                    current, destination
                )
                for destination in remaining
            }

            reachable = {
                destination: path
                for destination, path in paths.items()
                if path is not None
            }

            # replace start
            # if not reachable:
            #     raise ValueError(
            #         "No reachable destination remains."
            #     )
            # replace end
            if not reachable:
                blocked_destinations = [
                    destination
                    for destination in remaining
                    if self.topology.IsBlocked(destination)
                ]

                if blocked_destinations:
                    raise ValueError("destination is blocked")

                raise ValueError("No reachable destination remains.")


            destination = min(
                reachable,
                key=lambda location: len(reachable[location])
            )

            path = reachable[destination]

            route.extend(path[1:])
            total_distance += len(path) - 1

            current = destination
            remaining.remove(destination)

        return RouteResult(
            route=route,
            distance=total_distance,
            items=list(destinations)
        )

    def _find_path(self, start, destination):
        if self.topology.IsBlocked(destination):
            return None

        queue = deque([start])
        previous = {start: None}

        while queue:
            current = queue.popleft()

            if current == destination:
                return self._reconstruct_path(
                    previous, destination
                )

            for neighbor in self.topology.GetNeighbors(current):
                if neighbor not in previous:
                    previous[neighbor] = current
                    queue.append(neighbor)

        return None

    def _reconstruct_path(self, previous, destination):
        path = []
        current = destination

        while current is not None:
            path.append(current)
            current = previous[current]

        return list(reversed(path))