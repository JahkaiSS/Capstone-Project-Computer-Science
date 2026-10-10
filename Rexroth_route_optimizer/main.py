import tkinter as tk
from tkinter import ttk, messagebox
from models import Order, OrderItem
from topology import WarehouseTopology
from order_manager import generate_orders, optimize_orders, PICK_LOCATIONS, PUTAWAY_LOCATIONS

CELL_SIZE = 32


class WarehouseGUI:
    def __init__(self, root):
        self.root = root
        root.title('Warehouse Route Optimizer')
        root.geometry('1250x850')
        self.topology = WarehouseTopology()
        self.start_location = tk.StringVar(value='R02')
        self.capacity = tk.StringVar(value='30')
        self.order_count = tk.StringVar(value='6')
        self.min_items = tk.StringVar(value='1')
        self.max_items = tk.StringVar(value='9')
        self.orders = []
        self.result = None
        self.build_ui()
        self.generate()

    def build_ui(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text='Warehouse Route Optimizer', font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=8, sticky='w')
        settings = [('Start', self.start_location), ('Cart capacity', self.capacity),
                    ('Orders', self.order_count), ('Min items/order', self.min_items),
                    ('Max items/order', self.max_items)]
        for i, (label, variable) in enumerate(settings):
            ttk.Label(controls, text=label).grid(row=1, column=i, padx=4)
            if i == 0:
                ttk.Combobox(controls, textvariable=variable, values=list(self.topology.locations),
                             state='readonly', width=10).grid(row=2, column=i, padx=4)
            else:
                ttk.Entry(controls, textvariable=variable, width=10).grid(row=2, column=i, padx=4)
        ttk.Button(controls, text='Generate Orders', command=self.generate).grid(row=2, column=5, padx=5)
        ttk.Button(controls, text='Apply Edits', command=self.apply_edits).grid(row=2, column=6, padx=5)
        ttk.Button(controls, text='Optimize Run', command=self.optimize).grid(row=2, column=7, padx=5)

        self.status = ttk.Label(self.root, text='')
        self.status.pack(anchor='w', padx=12, pady=4)
        pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane, padding=8)
        pane.add(left, weight=3)
        pane.add(right, weight=2)

        self.canvas = tk.Canvas(left, background='white')
        vertical = ttk.Scrollbar(left, orient='vertical', command=self.canvas.yview)
        horizontal = ttk.Scrollbar(left, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<MouseWheel>', lambda e: self.canvas.yview_scroll(-int(e.delta / 120), 'units'))
        self.canvas.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))
        self.canvas.bind('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))

        ttk.Label(right, text='Orders (edit items and destination)', font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(right, text='Double-click Items or Destination to edit.').pack(anchor='w')
        self.tree = ttk.Treeview(right, columns=('order', 'items', 'destination', 'r2', 'r3'),
                                 show='headings', height=9)
        for name, width in [('order', 100), ('items', 60), ('destination', 95), ('r2', 50), ('r3', 50)]:
            self.tree.heading(name, text=name.upper())
            self.tree.column(name, width=width, anchor='center')
        self.tree.pack(fill='x', pady=5)
        self.tree.bind('<Double-1>', self.edit_cell)
        ttk.Label(right, text='Route actions', font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10, 0))
        self.details = tk.Text(right, wrap='word', height=20)
        self.details.pack(fill='both', expand=True)

    def generate(self):
        try:
            count, low, high = int(self.order_count.get()), int(self.min_items.get()), int(self.max_items.get())
            capacity = int(self.capacity.get())
            if not (1 <= count <= 8 and 1 <= low <= high <= capacity):
                raise ValueError
        except ValueError:
            messagebox.showerror('Invalid settings', 'Use 1–8 orders, positive cart capacity, and 1 <= min <= max <= capacity.')
            return
        self.orders = generate_orders(self.topology, count, low, high)
        self.refresh_orders()

    def refresh_orders(self):
        self.result = None
        self.tree.delete(*self.tree.get_children())
        for order in self.orders:
            r2 = sum(x.quantity for x in order.items if x.location.name == 'R2')
            r3 = sum(x.quantity for x in order.items if x.location.name == 'R3')
            self.tree.insert('', 'end', iid=order.number,
                             values=(order.number, order.quantity, order.destination.name, r2, r3))
        self.status.configure(text=f'{len(self.orders)} orders | {sum(o.quantity for o in self.orders)} items | Route not calculated')
        self.details.delete('1.0', 'end')
        self.details.insert('end', 'Generate or edit orders, then click Optimize Run.\n')
        self.draw_map()

    def edit_cell(self, event):
        row = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not row or column not in ('#2', '#3', '#4', '#5'):
            return
        bbox = self.tree.bbox(row, column)
        if not bbox:
            return
        x, y, width, height = bbox
        value = self.tree.set(row, column)
        if column == '#3':
            editor = ttk.Combobox(self.tree, values=PUTAWAY_LOCATIONS, state='readonly')
            editor.set(value)
        else:
            editor = ttk.Entry(self.tree)
            editor.insert(0, value)
        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()

        def save(event=None):
            new_value = editor.get()
            if column == '#3':
                if new_value not in PUTAWAY_LOCATIONS:
                    return
            else:
                try:
                    if int(new_value) < 0:
                        return
                except ValueError:
                    return
            self.tree.set(row, column, new_value)
            editor.destroy()
        editor.bind('<Return>', save)
        if column == '#3':
            editor.bind('<<ComboboxSelected>>', save)
        editor.bind('<Escape>', lambda e: editor.destroy())

    def apply_edits(self):
        try:
            capacity = int(self.capacity.get())
            if capacity < 1:
                raise ValueError('Cart capacity must be positive.')
            updated = []
            for old in self.orders:
                values = self.tree.item(old.number, 'values')
                number, total_text, destination_name, r2_text, r3_text = values
                total, r2, r3 = int(total_text), int(r2_text), int(r3_text)
                if min(total, r2, r3) < 0 or total != r2 + r3 or total == 0:
                    raise ValueError(f'{number}: Items must equal R2 + R3 and be positive.')
                if total > capacity:
                    raise ValueError(f'{number}: {total} items exceeds cart capacity {capacity}.')
                if destination_name not in PUTAWAY_LOCATIONS:
                    raise ValueError(f'{number}: invalid destination.')
                items = []
                for location, quantity in [('R2', r2), ('R3', r3)]:
                    for j in range(quantity):
                        items.append(OrderItem(number, f'{number}-{location}-{j+1:02}',
                                               self.topology.get_location(location), 1))
                updated.append(Order(number, self.topology.get_location(destination_name), items))
        except ValueError as exc:
            messagebox.showerror('Invalid order', str(exc))
            return False
        self.orders = updated
        self.refresh_orders()
        return True

    def optimize(self):
        if not self.apply_edits():
            return
        try:
            self.result = optimize_orders(self.topology, self.orders,
                                          self.start_location.get(), int(self.capacity.get()))
        except ValueError as exc:
            messagebox.showerror('Route unavailable', str(exc))
            return
        self.details.delete('1.0', 'end')
        self.details.insert('end', f'START: {self.start_location.get()}\n\n')
        for i, action in enumerate(self.result.actions, 1):
            self.details.insert('end', f'{i}. {action["type"]} {action["order"]} at {action["location"]}\n'
                                     f'   Quantity: {action["quantity"]} | Cart: {action["cart_load"]}/{self.capacity.get()}\n')
            if action['items']:
                self.details.insert('end', '   ' + ', '.join(x.item_number for x in action['items']) + '\n')
            self.details.insert('end', '\n')
        self.details.insert('end', f'TOTAL DISTANCE: {self.result.distance} grid units\n'
                                   f'FINAL CART LOAD: {self.result.actions[-1]["cart_load"] if self.result.actions else 0}\n')
        self.status.configure(text=f'{len(self.orders)} orders | {sum(o.quantity for o in self.orders)} items | Distance: {self.result.distance} grid units')
        self.draw_map()

    def point(self, row, column):
        return column * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2

    def draw_map(self):
        canvas = self.canvas
        canvas.delete('all')
        width = self.topology.width * CELL_SIZE
        height = self.topology.height * CELL_SIZE
        boundary = self.topology.door_row * CELL_SIZE
        canvas.configure(scrollregion=(0, 0, width, height))
        canvas.create_rectangle(0, 0, width, boundary, fill='#F1F7FF', outline='')
        canvas.create_rectangle(0, boundary, width, height, fill='#F2FFF2', outline='')
        canvas.create_text(width - 120, 105, text='Building A', font=('Arial', 20, 'bold'))
        canvas.create_text(width - 120, height - 100, text='Building B', font=('Arial', 20, 'bold'))
        canvas.create_line(0, boundary, width, boundary, fill='#555555', width=4, dash=(20, 12))
        canvas.create_text(width - 95, boundary - 20, text='Garage Door')
        for row, column in self.topology.blocked:
            x, y = self.point(row, column)
            half = CELL_SIZE // 2
            canvas.create_rectangle(x-half, y-half, x+half, y+half, fill='#E57373')
        if self.result and len(self.result.route) > 1:
            points = []
            for row, column in self.result.route:
                points.extend(self.point(row, column))
            canvas.create_line(*points, fill='#E53935', width=4, arrow=tk.LAST)
        counts = {name: 0 for name in self.topology.locations}
        for order in self.orders:
            counts[order.destination.name] += 1
            for item in order.items:
                counts[item.location.name] += item.quantity
        colors = {'R2': '#FFCC80', 'R3': '#FFCC80', 'Stacks': '#90CAF9', 'SRR': '#CE93D8'}
        for name, location in self.topology.locations.items():
            x, y = self.point(location.row, location.column)
            rx, ry = (75, 55) if name == 'Stacks' else (55, 40)
            canvas.create_oval(x-rx, y-ry, x+rx, y+ry, fill=colors[name], outline='#333333', width=3)
            canvas.create_text(x, y-12, text=name, font=('Arial', 14, 'bold'))
            description = f'{counts[name]} items' if name in PICK_LOCATIONS else f'{counts[name]} orders'
            canvas.create_text(x, y+12, text=description, font=('Arial', 10))


def main():
    root = tk.Tk()
    WarehouseGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
