# config!

"""Configuration for the warehouse route-optimizer demonstration."""

GRID_ROWS = 10
GRID_COLUMNS = 14
CELL_SIZE = 42
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
START_ROW = 0
START_COLUMN = 0
MAX_ORDER_LENGTH = 20

# Demonstration-only building connection. Replace these with verified Rexroth
# crossing/door locations before using the route as an operational instruction.
BUILDING_TRANSITIONS = [
    (("A", 9, 13), ("B", 0, 0)),
]
