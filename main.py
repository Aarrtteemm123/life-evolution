import random
from world import World
from gene import Gene
from trigger import Trigger
from action import Action
from cell import Cell
from substance import Substance

# === Константы симуляции ===
WORLD_WIDTH = 100
WORLD_HEIGHT = 100
CELL_COUNT = 20
INITIAL_SUBSTANCES = 200
SIMULATION_STEPS = 50


def random_substance() -> Substance:
    """Создаёт случайное вещество."""
    name = random.choice(["glucose", "signal_A", "toxin_X", "nutrient_B"])
    type_ = random.choice([Substance.ORGANIC, Substance.INORGANIC, Substance.TOXIN])
    concentration = random.uniform(0.1, 2.0)
    energy = random.uniform(0.0, 5.0)
    return Substance(name, type_, concentration, energy)


def random_gene() -> Gene:
    """Создаёт случайный ген."""
    receptor = random.choice(["energy", "glucose", "signal_A"])
    threshold = random.uniform(0.5, 5.0)
    mode = random.choice([Trigger.LESS, Trigger.GREATER])
    trigger = Trigger(threshold, mode)

    action_type = random.choice([
        Action.DIVIDE, Action.EMIT, Action.ABSORB,
        Action.TRANSFER, Action.MOVE
    ])

    action = Action(
        type_=action_type,
        power=random.uniform(0.5, 2.0),
        substance_name=random.choice(["glucose", "signal_A", "toxin_X"]),
        direction=(random.uniform(-1, 1), random.uniform(-1, 1))
    )

    return Gene(
        receptor=receptor,
        trigger=trigger,
        action=action,
        efficiency=random.uniform(0.5, 1.5),
        active=True
    )


def random_cell(x: int, y: int) -> Cell:
    """Создаёт клетку с случайным набором генов."""
    cell = Cell(position=(x + random.random(), y + random.random()))
    cell.energy = random.uniform(5.0, 15.0)
    cell.health = random.uniform(5.0, 10.0)
    for _ in range(random.randint(1, 3)):
        cell.genes.append(random_gene())
    return cell


def populate_world(world: World):
    """Заполняет мир веществами и клетками."""
    # 1. Заполнение сетки веществ
    for _ in range(INITIAL_SUBSTANCES):
        x = random.randint(0, world.grid.width - 1)
        y = random.randint(0, world.grid.height - 1)
        world.grid.add_substance(x, y, random_substance())

    # 2. Создание клеток
    for _ in range(CELL_COUNT):
        x = random.randint(0, world.grid.width - 1)
        y = random.randint(0, world.grid.height - 1)
        cell = random_cell(x, y)
        world.cells.append(cell)


import time

def run_simulation():
    """Основной цикл симуляции."""
    print("🔬 Инициализация мира...")
    world = World(WORLD_WIDTH, WORLD_HEIGHT)
    populate_world(world)

    print(f"🌎 Мир создан: {len(world.cells)} клеток, {len(world.grid.grid)} активных ячеек веществ")

    print("🚀 Запуск симуляции...")
    start_time = time.perf_counter()

    last_time = start_time
    for step in range(SIMULATION_STEPS):
        step_start = time.perf_counter()

        world.update()

        step_end = time.perf_counter()
        step_duration = step_end - step_start

        if step % 10 == 0 and step > 0:
            now = time.perf_counter()
            elapsed = now - last_time
            ticks_per_sec = 10 / elapsed
            avg_step_time = elapsed / 10
            print(f"Step {step:4d} | tick={world.tick:4d} | "
                  f"cells={len(world.cells):3d} | "
                  f"{ticks_per_sec:.2f} tps | {avg_step_time*1000:.2f} ms/tick")
            last_time = now

    total_time = time.perf_counter() - start_time
    avg_tick_time = total_time / SIMULATION_STEPS
    print("⏱️ Всего времени:", f"{total_time:.2f}s")
    print("⚡ Средняя скорость:", f"{1/avg_tick_time:.2f} тиков/сек ({avg_tick_time*1000:.2f} мс/тик)")

    print("💾 Сохранение состояния...")
    world.save("simulation_state.json")

    print("✅ Симуляция завершена и сохранена в simulation_state.json")

    # проверка загрузки
    restored = World.load("simulation_state.json")
    print("♻️ Загрузка успешна! Tick:", restored.tick)


if __name__ == "__main__":
    run_simulation()
