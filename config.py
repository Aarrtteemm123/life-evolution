# === Константы симуляции ===
WORLD_WIDTH = 40
WORLD_HEIGHT = 40
CELL_COUNT = 10
CELLS_LIMIT = 50
CELL_RADIUS = 0.5  # радиус клетки для физики столкновений
CELL_REPULSION_FORCE = 1.5  # сила отталкивания при столкновении
# === Конфигурация распределения веществ ===
SUBSTANCE_DISTRIBUTION = {
    "ORGANIC": 500,     # количество органических веществ
    "TOXIN": 10,       # количество токсинов
    "INORGANIC": 10    # количество неорганических соединений
}
UNIQUE_INORGANIC_COUNT = 10 # количество уникальных неорганических соединений
SIMULATION_STEPS = 1000
FPS = 60
FRAME_TIME = 1 / FPS
SAVES_DIR = "saves/"
INCLUDE_BASE_GENES = True
# === вероятность появления органики в каждой ячейке за тик (0.001 = 0.1%) ===
ORGANIC_SPAWN_PROBABILITY_PER_CELL_PER_TICK = 0.0001
# === Конфигурация рассеивания веществ ===
SUBSTANCE_DIFFUSION_RATE = 0.1  # скорость рассеивания (0.0 = отключено, 0.1 = 10% рассеивается в соседние ячейки)

# === Органические вещества (питательные) ===
ORGANIC_TYPES = [
    {"name": "ORGANIC_0", "energy": 1.5, "concentration": (0.1, 10.0)},
    {"name": "ORGANIC_1", "energy": 3.0, "concentration": (0.1, 10.0)},
    {"name": "ORGANIC_2", "energy": 5.0, "concentration": (0.1, 10.0)},
]

# === Токсины (наносят вред) ===
TOXIN_TYPES = [
    {"name": "TOXIN_0", "energy": 1.0, "concentration": (0.1, 10.0)},  # слабый
    {"name": "TOXIN_1", "energy": 3.0, "concentration": (0.1, 10.0)},
    {"name": "TOXIN_2", "energy": 4.0, "concentration": (0.1, 10.0)},
]

INORGANIC_TYPES = [
    {"name": f"INORGANIC_{i}", "energy": 0.5, "concentration": (0.1, 10.0)}
    for i in range(0, UNIQUE_INORGANIC_COUNT)
]

ALL_SUBSTANCE_NAMES = [
    "ORGANIC_0", "ORGANIC_1", "ORGANIC_2",
    "TOXIN_0", "TOXIN_1", "TOXIN_2",
    *[f"INORGANIC_{i}" for i in range(0, UNIQUE_INORGANIC_COUNT)]
]

SUBSTANCES = {}