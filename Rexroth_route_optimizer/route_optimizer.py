from abc import ABC, abstractmethod

from models import Building, OrderItem


class IWMSIntegration(ABC):

    @abstractmethod
    def GetOrderItems(self, order_number):
        pass

    @abstractmethod
    def UpdateInventoryStock(self, item_number, quantity):
        pass


class DemoWMSIntegration(IWMSIntegration):

    def __init__(self, topology):
        self.topology = topology

        self.orders = {
            "1001": [
                OrderItem(
                    "1001",
                    "R9000123",
                    topology.get_location(Building.A, 2, 8),
                    1,
                ),
                OrderItem(
                    "1001",
                    "R9000148",
                    topology.get_location(Building.A, 7, 2),
                    2,
                ),
            ],
            "1002": [
                OrderItem(
                    "1002",
                    "R9000231",
                    topology.get_location(Building.B, 2, 5),
                    1,
                ),
            ],
            "1003": [
                OrderItem(
                    "1003",
                    "R9000314",
                    topology.get_location(Building.B, 8, 11),
                    4,
                ),
            ],
            "1004": [
                OrderItem(
                    "1004",
                    "R9000123",
                    topology.get_location(Building.A, 2, 8),
                    1,
                ),
                OrderItem(
                    "1004",
                    "R9000231",
                    topology.get_location(Building.B, 2, 5),
                    1,
                ),
            ],
        }

    def GetOrderItems(self, order_number):
        if order_number not in self.orders:
            raise ValueError(
                f"Order number {order_number} was not found."
            )

        return list(self.orders[order_number])

    def UpdateInventoryStock(self, item_number, quantity):
        print(f"Inventory update: {item_number} x{quantity}")


class IOrderBatcher(ABC):

    @abstractmethod
    def CreateBatches(self, order_numbers):
        pass


class OrderBatcher(IOrderBatcher):

    def __init__(self, wms):
        self.wms = wms

    def CreateBatches(self, order_numbers):
        if not order_numbers:
            raise ValueError("No orders were provided.")

        batch = []

        for order_number in order_numbers:
            if not order_number.isdigit():
                raise ValueError("Order number must contain digits only.")

            batch.extend(self.wms.GetOrderItems(order_number))

        return batch