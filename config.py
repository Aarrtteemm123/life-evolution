# === Константы симуляции ===
WORLD_WIDTH = 100
WORLD_HEIGHT = 100
CELL_COUNT = 100
# === Конфигурация распределения веществ ===
SUBSTANCE_DISTRIBUTION = {
    "ORGANIC": 500,     # количество органических веществ
    "TOXIN": 100,       # количество токсинов
    "INORGANIC": 50    # количество неорганических соединений
}
SIMULATION_STEPS = 100
FPS = 10
SAVES_DIR = "saves/"
INCLUDE_BASE_GENES = True

# === Органические вещества (питательные) ===
ORGANIC_TYPES = [
    {"name": "ORGANIC_0", "energy": 1.5, "concentration": (0.1, 10.0)},
    {"name": "ORGANIC_1", "energy": 3.0, "concentration": (0.1, 10.0)},
    {"name": "ORGANIC_2", "energy": 5.0, "concentration": (0.1, 10.0)},
]

# === Токсины (наносят вред, отрицательная энергия) ===
TOXIN_TYPES = [
    {"name": "TOXIN_0", "energy": -1.0, "concentration": (0.1, 10.0)},  # слабый
    {"name": "TOXIN_1", "energy": -3.0, "concentration": (0.1, 10.0)},
    {"name": "TOXIN_2", "energy": -4.0, "concentration": (0.1, 10.0)},
    {"name": "TOXIN_3", "energy": -5.0, "concentration": (0.1, 10.0)},
    {"name": "TOXIN_4", "energy": -6.0, "concentration": (0.1, 10.0)},  # сильный
]

INORGANIC_TYPES = [
    {"name": f"INORGANIC_{i}", "energy": 0.5, "concentration": (0.1, 10.0)}
    for i in range(0, SUBSTANCE_DISTRIBUTION.get("INORGANIC"))
]

ALL_SUBSTANCE_NAMES = [
    "ORGANIC_0", "ORGANIC_1", "ORGANIC_2",
    "TOXIN_0", "TOXIN_1", "TOXIN_2", "TOXIN_3", "TOXIN_4",
    *[f"INORGANIC_{i}" for i in range(0, SUBSTANCE_DISTRIBUTION.get("INORGANIC"))]
]