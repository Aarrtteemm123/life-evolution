# === Константы симуляции ===
WORLD_WIDTH = 100
WORLD_HEIGHT = 100
CELL_COUNT = 100
INITIAL_SUBSTANCES = 100
SIMULATION_STEPS = 100
FPS = 10
SAVES_DIR = "saves/"

ORGANIC_TYPES = [
    {"name": "ORGANIC_0", "energy": (1.0, 2.0), "concentration": (0.5, 1.0)},
    {"name": "ORGANIC_1", "energy": (2.0, 4.0), "concentration": (0.3, 0.8)},
    {"name": "ORGANIC_2", "energy": (4.0, 6.0), "concentration": (0.1, 0.5)},
]

TOXIN_TYPES = [
    {"name": "TOXIN_0", "energy": (-1.0, 0.0), "concentration": (0.1, 0.3)},  # слабый
    {"name": "TOXIN_1", "energy": (-2.0, -0.5), "concentration": (0.1, 0.4)},
    {"name": "TOXIN_2", "energy": (-3.0, -1.0), "concentration": (0.2, 0.6)},
    {"name": "TOXIN_3", "energy": (-4.0, -2.0), "concentration": (0.3, 0.8)},
    {"name": "TOXIN_4", "energy": (-5.0, -3.0), "concentration": (0.4, 1.0)},  # сильный
]

INORGANIC_COUNT = 30
INORGANIC_TYPES = [
    {"name": f"INORGANIC_{i}", "energy": (0.0, 1.0), "concentration": (0.2, 1.5)}
    for i in range(0, INORGANIC_COUNT)
]

ALL_SUBSTANCE_NAMES = [
    "ORGANIC_0", "ORGANIC_1", "ORGANIC_2",
    "TOXIN_0", "TOXIN_1", "TOXIN_2", "TOXIN_3", "TOXIN_4",
    *[f"INORGANIC_{i}" for i in range(0, INORGANIC_COUNT)]
]