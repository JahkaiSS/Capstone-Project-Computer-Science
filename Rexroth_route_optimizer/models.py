from dataclasses import dataclass, field
from enum import Enum


class Building(Enum):
    A = 'Building A'
    B = 'Building B'


@dataclass(frozen=True)
class Location:
    building: Building
    row: int
    column: int
    name: str = ''

    def display_name(self):
        return f'{self.building.value} - {self.name}' if self.name else f'{self.building.value} ({self.row}, {self.column})'


@dataclass(frozen=True)
class OrderItem:
    order_number: str
    item_number: str
    location: Location
    quantity: int = 1


@dataclass
class Order:
    number: str
    destination: Location
    items: list[OrderItem] = field(default_factory=list)

    @property
    def quantity(self):
        return sum(item.quantity for item in self.items)


@dataclass
class RouteResult:
    route: list
    distance: int
    items: list = field(default_factory=list)
    actions: list = field(default_factory=list)
