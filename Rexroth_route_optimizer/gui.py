import itertools
import random
import tkinter as tk
from tkinter import ttk, messagebox

from topology import WarehouseTopology


CELL_SIZE = 32

PICK_LOCATIONS = ("R2", "R3")
PUTAWAY_LOCATIONS = ("Stacks", "SRR")


class WarehouseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Warehouse Route Optimizer")
        self.root.geometry("1250x850")

        self.topology = WarehouseTopology()

        self.location_names = list(
            self.topology.locations.keys()
        )

        self.start_location = tk.StringVar(value="R02")
        self.random_total = tk.StringVar(value="20")

        self.item_counts = {
            name: tk.StringVar(value="0")
            for name in self.location_names
        }

        self.items = []
        self.route_path = []
        self.stop_order = []

        self.create_widgets()
        self.generate_run()

    def operation_for(self, location):
        if location in PICK_LOCATIONS:
            return "PICK"

        if location in PUTAWAY_LOCATIONS:
            return "PUT AWAY"

        raise ValueError(
            f"Unknown warehouse location: {location}"
        )

    def create_widgets(self):
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill=tk.X)

        ttk.Label(
            controls,
            text="Warehouse Route Optimizer",
            font=("Arial", 16, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            sticky=tk.W,
            pady=5
        )

        ttk.Label(
            controls,
            text="Starting Location:"
        ).grid(row=1, column=0, padx=5)

        ttk.Combobox(
            controls,
            textvariable=self.start_location,
            values=self.location_names,
            state="readonly",
            width=12
        ).grid(row=1, column=1, padx=5)

        ttk.Label(
            controls,
            text="Random Item Total:"
        ).grid(row=1, column=2, padx=5)

        ttk.Entry(
            controls,
            textvariable=self.random_total,
            width=8
        ).grid(row=1, column=3, padx=5)

        ttk.Button(
            controls,
            text="Generate Random",
            command=self.generate_run
        ).grid(row=1, column=4, padx=5)

        ttk.Button(
            controls,
            text="Optimize Run",
            command=self.optimize_run
        ).grid(row=1, column=5, padx=5)

        ttk.Label(
            controls,
            text="Items per location:",
            font=("Arial", 10, "bold")
        ).grid(
            row=2,
            column=0,
            sticky=tk.W,
            pady=10
        )

        count_frame = ttk.Frame(controls)
        count_frame.grid(
            row=3,
            column=0,
            columnspan=6,
            sticky=tk.W
        )

        for index, name in enumerate(
            self.location_names
        ):
            operation = self.operation_for(name)

            ttk.Label(
                count_frame,
                text=f"{name} ({operation}):"
            ).grid(
                row=0,
                column=index * 2,
                padx=5
            )

            ttk.Entry(
                count_frame,
                textvariable=self.item_counts[name],
                width=6
            ).grid(
                row=0,
                column=index * 2 + 1,
                padx=5
            )

        ttk.Button(
            controls,
            text="Apply Manual Counts",
            command=self.apply_manual_counts
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=10
        )

        ttk.Button(
            controls,
            text="Clear Route",
            command=self.clear_route
        ).grid(
            row=4,
            column=2,
            columnspan=2,
            pady=10
        )

        self.status_label = ttk.Label(
            self.root,
            text="",
            font=("Arial", 11)
        )
        self.status_label.pack(
            anchor=tk.W,
            padx=15,
            pady=5
        )

        main = ttk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL
        )
        main.pack(fill=tk.BOTH, expand=True)

        map_frame = ttk.Frame(main)
        main.add(map_frame, weight=3)

        self.canvas = tk.Canvas(
            map_frame,
            background="white"
        )

        vertical = ttk.Scrollbar(
            map_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )

        horizontal = ttk.Scrollbar(
            map_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )

        self.canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set
        )

        vertical.pack(side=tk.RIGHT, fill=tk.Y)
        horizontal.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        self.canvas.bind(
            "<MouseWheel>",
            self.on_mousewheel
        )

        info_frame = ttk.Frame(main, padding=10)
        main.add(info_frame, weight=1)

        ttk.Label(
            info_frame,
            text="Warehouse Run",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W)

        self.item_tree = ttk.Treeview(
            info_frame,
            columns=(
                "item",
                "location",
                "operation",
                "quantity"
            ),
            show="headings",
            height=12
        )

        columns = [
            ("item", "Item", 100),
            ("location", "Location", 75),
            ("operation", "Operation", 90),
            ("quantity", "Qty", 45)
        ]

        for column, title, width in columns:
            self.item_tree.heading(
                column, text=title
            )
            self.item_tree.column(
                column, width=width
            )

        self.item_tree.pack(
            fill=tk.BOTH,
            expand=True,
            pady=5
        )

        ttk.Label(
            info_frame,
            text="Optimized Work Sequence",
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))

        self.route_text = tk.Text(
            info_frame,
            height=13,
            width=35,
            wrap=tk.WORD
        )
        self.route_text.pack(
            fill=tk.BOTH,
            expand=True
        )

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(
            -int(event.delta / 120),
            "units"
        )

    def generate_run(self):
        try:
            total = int(self.random_total.get())

            if total < 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Total",
                "Enter a nonnegative whole number."
            )
            return

        counts = {
            name: 0
            for name in self.location_names
        }

        for _ in range(total):
            chosen = random.choice(
                self.location_names
            )
            counts[chosen] += 1

        for name, count in counts.items():
            self.item_counts[name].set(str(count))

        self.build_items(counts)

    def apply_manual_counts(self):
        counts = {}

        try:
            for name in self.location_names:
                count = int(
                    self.item_counts[name].get()
                )

                if count < 0:
                    raise ValueError

                counts[name] = count

        except ValueError:
            messagebox.showerror(
                "Invalid Count",
                "Each location must have a "
                "nonnegative whole number."
            )
            return

        self.build_items(counts)

    def build_items(self, counts):
        self.items = []
        self.route_path = []
        self.stop_order = []

        number = 1

        for location, count in counts.items():
            operation = self.operation_for(location)

            for _ in range(count):
                self.items.append({
                    "item_number": f"ITEM-{number:03}",
                    "location": location,
                    "operation": operation,
                    "quantity": 1
                })
                number += 1

        self.refresh_items()

        self.route_text.delete("1.0", tk.END)
        self.route_text.insert(
            tk.END,
            "Run created.\n"
            "Click Optimize Run to calculate "
            "the work sequence."
        )

        pick_count = sum(
            1 for item in self.items
            if item["operation"] == "PICK"
        )

        putaway_count = sum(
            1 for item in self.items
            if item["operation"] == "PUT AWAY"
        )

        self.status_label.configure(
            text=(
                f"{len(self.items)} total items | "
                f"{pick_count} picks | "
                f"{putaway_count} put-aways"
            )
        )

        self.draw_warehouse()

    def refresh_items(self):
        for row in self.item_tree.get_children():
            self.item_tree.delete(row)

        for item in self.items:
            self.item_tree.insert(
                "",
                tk.END,
                values=(
                    item["item_number"],
                    item["location"],
                    item["operation"],
                    item["quantity"]
                )
            )

    def optimize_run(self):
        if not self.items:
            messagebox.showwarning(
                "No Items",
                "Add items before optimizing."
            )
            return

        start_name = self.start_location.get()

        required = list(dict.fromkeys(
            item["location"]
            for item in self.items
        ))

        remaining = [
            name for name in required
            if name != start_name
        ]

        best_distance = float("inf")
        best_order = None
        best_path = None

        for permutation in itertools.permutations(
            remaining
        ):
            order = [start_name] + list(permutation)

            total_distance = 0
            full_path = []
            valid = True

            for i in range(len(order) - 1):
                first = self.topology.get_location(
                    order[i]
                )
                second = self.topology.get_location(
                    order[i + 1]
                )

                segment = self.topology.find_path(
                    first, second
                )

                if segment is None:
                    valid = False
                    break

                total_distance += len(segment) - 1

                if full_path:
                    full_path.extend(segment[1:])
                else:
                    full_path.extend(segment)

            if valid and total_distance < best_distance:
                best_distance = total_distance
                best_order = order
                best_path = full_path

        if best_order is None:
            messagebox.showerror(
                "No Valid Route",
                "The locations cannot all be reached."
            )
            return

        self.stop_order = best_order
        self.route_path = best_path or []

        self.show_route_details(best_distance)
        self.draw_warehouse()

    def show_route_details(self, distance):
        self.route_text.delete("1.0", tk.END)

        for index, name in enumerate(
            self.stop_order, start=1
        ):
            location_items = [
                item for item in self.items
                if item["location"] == name
            ]

            operation = self.operation_for(name)

            self.route_text.insert(
                tk.END,
                f"STOP {index}: {name}\n"
                f"Operation: {operation}\n"
                f"Items: {len(location_items)}\n"
            )

            for item in location_items:
                self.route_text.insert(
                    tk.END,
                    f"  {item['item_number']}"
                    f"  Qty: {item['quantity']}\n"
                )

            self.route_text.insert(tk.END, "\n")

        pick_count = sum(
            item["quantity"]
            for item in self.items
            if item["operation"] == "PICK"
        )

        putaway_count = sum(
            item["quantity"]
            for item in self.items
            if item["operation"] == "PUT AWAY"
        )

        self.route_text.insert(
            tk.END,
            f"TOTAL ITEMS: {len(self.items)}\n"
            f"PICK QUANTITY: {pick_count}\n"
            f"PUT-AWAY QUANTITY: {putaway_count}\n"
            f"TOTAL STOPS: {len(self.stop_order)}\n"
            f"DISTANCE: {distance} grid units\n"
        )

        self.status_label.configure(
            text=(
                f"{len(self.items)} items | "
                f"{len(self.stop_order)} stops | "
                f"{distance} grid units"
            )
        )

    def clear_route(self):
        self.route_path = []
        self.stop_order = []

        self.route_text.delete("1.0", tk.END)

        self.status_label.configure(
            text=f"{len(self.items)} items | Route cleared"
        )

        self.draw_warehouse()

    def grid_to_canvas(self, row, column):
        return (
            column * CELL_SIZE + CELL_SIZE // 2,
            row * CELL_SIZE + CELL_SIZE // 2
        )

    def draw_warehouse(self):
        self.canvas.delete("all")

        width = self.topology.width * CELL_SIZE
        height = self.topology.height * CELL_SIZE
        boundary = self.topology.door_row * CELL_SIZE

        self.canvas.configure(
            scrollregion=(0, 0, width, height)
        )

        self.canvas.create_rectangle(
            0, 0, width, boundary,
            fill="#F1F7FF",
            outline=""
        )

        self.canvas.create_rectangle(
            0, boundary, width, height,
            fill="#F2FFF2",
            outline=""
        )

        self.canvas.create_text(
            width - 130, 110,
            text="Building A",
            font=("Arial", 22, "bold")
        )

        self.canvas.create_text(
            width - 130, height - 110,
            text="Building B",
            font=("Arial", 22, "bold")
        )

        self.canvas.create_line(
            0, boundary,
            width, boundary,
            fill="#555555",
            width=4,
            dash=(20, 12)
        )

        self.canvas.create_text(
            width - 100, boundary - 20,
            text="Garage Door",
            font=("Arial", 11, "bold")
        )

        self.draw_route()
        self.draw_locations()

    def draw_route(self):
        if len(self.route_path) < 2:
            return

        points = []

        for row, column in self.route_path:
            x, y = self.grid_to_canvas(
                row, column
            )
            points.extend((x, y))

        self.canvas.create_line(
            *points,
            fill="#E53935",
            width=4,
            arrow=tk.LAST,
            arrowshape=(12, 15, 6)
        )

    def draw_locations(self):
        colors = {
            "R02": "#FFCC80",
            "R03": "#FFCC80",
            "Stacks": "#90CAF9",
            "SRR": "#CE93D8"
        }

        for name, location in (
            self.topology.locations.items()
        ):
            x, y = self.grid_to_canvas(
                location.row,
                location.column
            )

            if name == "Stacks":
                rx, ry = 75, 55
            else:
                rx, ry = 55, 40

            self.canvas.create_oval(
                x - rx, y - ry,
                x + rx, y + ry,
                fill=colors.get(name, "white"),
                outline="#333333",
                width=3
            )

            count = sum(
                1 for item in self.items
                if item["location"] == name
            )

            operation = self.operation_for(name)

            self.canvas.create_text(
                x, y - 13,
                text=name,
                font=("Arial", 15, "bold")
            )

            self.canvas.create_text(
                x, y + 7,
                text=operation,
                font=("Arial", 9, "bold")
            )

            self.canvas.create_text(
                x, y + 24,
                text=f"{count} items",
                font=("Arial", 10)
            )

            if name in self.stop_order:
                number = self.stop_order.index(name) + 1

                self.canvas.create_text(
                    x + rx - 5,
                    y - ry - 10,
                    text=f"Stop {number}",
                    font=("Arial", 11, "bold"),
                    fill="#C62828"
                )


def main():
    root = tk.Tk()
    WarehouseGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()