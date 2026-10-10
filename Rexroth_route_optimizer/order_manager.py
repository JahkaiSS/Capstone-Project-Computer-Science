import heapq
import random
from models import Order, OrderItem, RouteResult

PICK_LOCATIONS = ('R2', 'R3')
PUTAWAY_LOCATIONS = ('Stacks', 'SRR')


def generate_orders(topology, count=6, min_items=1, max_items=9, rng=None):
    rng = rng or random.Random()
    orders = []
    for index in range(1, count + 1):
        number = f'ORD-{index:03d}'
        destination = topology.get_location(rng.choice(PUTAWAY_LOCATIONS))
        quantity = rng.randint(min_items, max_items)
        items = [OrderItem(number, f'{number}-ITEM-{j:02d}',
                           topology.get_location(rng.choice(PICK_LOCATIONS)), 1)
                 for j in range(1, quantity + 1)]
        orders.append(Order(number, destination, items))
    return orders


def optimize_orders(topology, orders, start_name='R2', capacity=30):
    """Exact shortest-distance route for modest numbers of orders.

    State tracks current location, collected pick-group mask, and delivered
    order mask. Each group is all items for one order at one pick location.
    """
    if capacity <= 0:
        raise ValueError('Cart capacity must be positive.')
    if start_name not in topology.locations:
        raise ValueError('Unknown starting location.')
    if not orders:
        return RouteResult([], 0, [], [])
    if len(orders) > 8:
        raise ValueError('Exact optimizer supports at most 8 orders per run.')

    groups = []
    for i, order in enumerate(orders):
        if not order.items:
            raise ValueError(f'{order.number} has no items.')
        if order.quantity > capacity:
            raise ValueError(f'{order.number} contains {order.quantity} items, exceeding cart capacity {capacity}.')
        if order.destination.name not in PUTAWAY_LOCATIONS:
            raise ValueError(f'{order.number} has an invalid put-away destination.')
        by_location = {}
        for item in order.items:
            if item.order_number != order.number or item.quantity <= 0:
                raise ValueError(f'Invalid item in {order.number}.')
            if item.location.name not in PICK_LOCATIONS:
                raise ValueError(f'Invalid picking location in {order.number}.')
            by_location.setdefault(item.location.name, []).append(item)
        for name, items in by_location.items():
            groups.append((i, name, tuple(items), sum(item.quantity for item in items)))

    # Distances between named stops; topology handles blocked cells.
    relevant = {start_name} | {g[1] for g in groups} | {o.destination.name for o in orders}
    paths = {}
    for a in relevant:
        for b in relevant:
            path = topology.find_path(topology.get_location(a), topology.get_location(b))
            if path is not None:
                paths[a, b] = path

    full_pick_mask = (1 << len(groups)) - 1
    full_delivery_mask = (1 << len(orders)) - 1
    order_group_masks = [0] * len(orders)
    for j, (order_index, _, _, _) in enumerate(groups):
        order_group_masks[order_index] |= 1 << j

    start = (start_name, 0, 0)
    best = {start: 0}
    parent = {}
    heap = [(0, 0, start)]
    sequence = 0
    goal = None

    while heap:
        distance, _, state = heapq.heappop(heap)
        if distance != best[state]:
            continue
        current, picked, delivered = state
        if picked == full_pick_mask and delivered == full_delivery_mask:
            goal = state
            break

        cart_load = sum(g[3] for j, g in enumerate(groups)
                        if picked & (1 << j) and not (delivered & (1 << g[0])))
        candidates = []
        for j, (order_index, location, items, quantity) in enumerate(groups):
            if not (picked & (1 << j)) and cart_load + quantity <= capacity:
                candidates.append((location, picked | (1 << j), delivered,
                                   ('PICK', orders[order_index].number, location, quantity, items)))
        for i, order in enumerate(orders):
            if (not (delivered & (1 << i))
                    and picked & order_group_masks[i] == order_group_masks[i]):
                candidates.append((order.destination.name, picked, delivered | (1 << i),
                                   ('PUT AWAY', order.number, order.destination.name, order.quantity, ())))

        for location, new_picked, new_delivered, action in candidates:
            path = paths.get((current, location))
            if path is None:
                continue
            next_state = (location, new_picked, new_delivered)
            next_distance = distance + len(path) - 1
            if next_distance < best.get(next_state, float('inf')):
                best[next_state] = next_distance
                parent[next_state] = (state, action)
                sequence += 1
                heapq.heappush(heap, (next_distance, sequence, next_state))

    if goal is None:
        raise ValueError('No valid route satisfies the cart capacity and warehouse paths.')

    steps = []
    cursor = goal
    while cursor != start:
        previous, action = parent[cursor]
        steps.append((previous[0], cursor[0], action))
        cursor = previous
    steps.reverse()

    full_route = [(topology.get_location(start_name).row,
                   topology.get_location(start_name).column)]
    actions = []
    load = 0
    for source, destination, action in steps:
        segment = paths[source, destination]
        full_route.extend(segment[1:])
        kind, number, location, quantity, items = action
        load += quantity if kind == 'PICK' else -quantity
        actions.append({'type': kind, 'order': number, 'location': location,
                        'quantity': quantity, 'items': list(items), 'cart_load': load})
    return RouteResult(full_route, best[goal], [item for order in orders for item in order.items], actions)
