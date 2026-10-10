from collections import deque
from models import Building, Location


class WarehouseTopology:
    WIDTH = 24
    HEIGHT = 24
    DOOR_ROW = 12

    def __init__(self):
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.door_row = self.DOOR_ROW
        self.blocked = set()
        self.locations = {
            'R2': Location(Building.A, 2, 6, 'R2'),
            'R3': Location(Building.A, 2, 12, 'R3'),
            'Stacks': Location(Building.A, 7, 3, 'Stacks'),
            'SRR': Location(Building.B, 19, 9, 'SRR'),
        }

    def get_location(self, name):
        return self.locations.get(name)

    def get_locations(self):
        return list(self.locations.values())

    def is_valid(self, row, column):
        return 0 <= row < self.height and 0 <= column < self.width

    def is_blocked(self, row, column):
        return (row, column) in self.blocked

    def block_location(self, row, column):
        if self.is_valid(row, column):
            self.blocked.add((row, column))

    def unblock_location(self, row, column):
        self.blocked.discard((row, column))

    def get_neighbors(self, row, column):
        return [(r, c) for r, c in ((row-1,column),(row+1,column),(row,column-1),(row,column+1))
                if self.is_valid(r,c) and not self.is_blocked(r,c)]

    def find_path(self, start, end):
        source = (start.row, start.column)
        target = (end.row, end.column)
        if not self.is_valid(*source) or not self.is_valid(*target):
            return None
        if self.is_blocked(*source) or self.is_blocked(*target):
            return None
        queue = deque([source])
        previous = {source: None}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbor in self.get_neighbors(*current):
                if neighbor not in previous:
                    previous[neighbor] = current
                    queue.append(neighbor)
        if target not in previous:
            return None
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = previous[current]
        return list(reversed(path))

    def get_distance(self, start, end):
        path = self.find_path(start, end)
        return None if path is None else len(path) - 1

    def get_distance_between(self, start, end):
        return self.get_distance(start, end)
