import os
import random
import time

from config import INITIAL_SUBSTANCES, CELL_COUNT, WORLD_WIDTH, WORLD_HEIGHT, SIMULATION_STEPS, SAVES_DIR, \
    ORGANIC_TYPES, TOXIN_TYPES, INORGANIC_TYPES, ALL_SUBSTANCE_NAMES
from models.gene import Gene
from models.trigger import Trigger
from models.action import Action
from models.cell import Cell
from models.substance import Substance
from models.world import World


def random_substance() -> Substance:
    """Создаёт случайное вещество из предопределённых категорий."""
    category = random.choices(
        [Substance.ORGANIC, Substance.TOXIN, Substance.INORGANIC],
        weights=[0.15, 0.25, 0.60],  # распределение вероятностей появления
        k=1
    )[0]

    if category == Substance.ORGANIC:
        data = random.choice(ORGANIC_TYPES)
        type_ = Substance.ORGANIC
    elif category == Substance.TOXIN:
        data = random.choice(TOXIN_TYPES)
        type_ = Substance.TOXIN
    else:
        data = random.choice(INORGANIC_TYPES)
        type_ = Substance.INORGANIC

    concentration = random.uniform(*data["concentration"])
    energy = random.uniform(*data["energy"])
    return Substance(data["name"], type_, concentration, energy)



def random_gene(all_substance_names: list[str]) -> Gene:
    """
    Создаёт случайный ген.
    Рецептор реагирует либо на 'energy', либо на конкретное вещество из среды.
    """

    # --- Рецептор ---
    # 80% генов реагируют на вещества, 20% — на внутреннюю энергию клетки
    if random.random() < 0.8 and all_substance_names:
        receptor = random.choice(all_substance_names)
    else:
        receptor = "energy"

    threshold = random.uniform(0.5, 5.0)
    mode = random.choice([Trigger.LESS, Trigger.GREATER, Trigger.EQUAL])
    trigger = Trigger(threshold, mode)

    # --- Действие ---
    action_type = random.choice([
        Action.DIVIDE, Action.EMIT, Action.ABSORB,
        Action.TRANSFER, Action.MOVE, Action.NONE
    ])

    # если действие связано с веществами — выберем из списка
    substance_name = None
    if action_type in (Action.EMIT, Action.ABSORB, Action.TRANSFER):
        substance_name = random.choice(all_substance_names) if all_substance_names else "ORGANIC_0"

    # направление имеет смысл только для MOVE
    direction = (
        (random.uniform(-1, 1), random.uniform(-1, 1))
        if action_type == Action.MOVE else (0.0, 0.0)
    )

    action = Action(
        type_=action_type,
        power=random.uniform(0.5, 2.0),
        substance_name=substance_name,
        direction=direction
    )

    return Gene(
        receptor=receptor,
        trigger=trigger,
        action=action,
        efficiency=random.uniform(0.5, 1.5),
        active=True
    )


def random_cell(x: int, y: int) -> Cell:
    """Создаёт клетку с случайным набором генов и начальными параметрами."""
    # Случайное смещение внутри клетки (чтобы не стояли ровно по сетке)
    cell = Cell(position=(x + random.random(), y + random.random()))

    # Начальные параметры
    cell.energy = random.uniform(20.0, 80.0)   # жизнеспособная энергия
    cell.health = random.uniform(40.0, 100.0)  # от частично повреждённой до здоровой

    # Количество генов: чаще 2–6, но иногда до 10
    gene_count = random.choices(
        population=range(1, 11),
        weights=[10, 15, 20, 20, 15, 10, 5, 3, 1, 1],  # экспоненциально убывающее
        k=1
    )[0]

    for _ in range(gene_count):
        cell.genes.append(random_gene(ALL_SUBSTANCE_NAMES))

    return cell


def populate_world(world: 'World'):
    """Заполняет мир веществами и клетками."""
    env = world.env

    # 1. Заполнение сетки веществ
    for _ in range(INITIAL_SUBSTANCES):
        x = random.randint(0, env.grid.width - 1)
        y = random.randint(0, env.grid.height - 1)
        env.add_substance(x, y, random_substance())

    # 2. Создание клеток
    for _ in range(CELL_COUNT):
        x = random.randint(0, env.grid.width - 1)
        y = random.randint(0, env.grid.height - 1)
        cell = random_cell(x, y)
        env.add_cell(cell)


def run_simulation():
    """Основной цикл симуляции."""
    print("🔬 Инициализация мира...")
    world = World(WORLD_WIDTH, WORLD_HEIGHT)
    populate_world(world)

    print(f"🌎 Мир создан: {len(world.env.cells)} клеток, "
          f"{len(world.env.grid.grid)} активных ячеек веществ")

    print("🚀 Запуск симуляции...")
    start_time = time.perf_counter()
    last_time = start_time

    for step in range(SIMULATION_STEPS):
        world.update()

        if step % 10 == 0 and step > 0:
            now = time.perf_counter()
            elapsed = now - last_time
            ticks_per_sec = 10 / elapsed
            avg_step_time = elapsed / 10

            print(f"Step {step:4d} | tick={world.tick:4d} | "
                  f"cells={len(world.env.cells):3d} | "
                  f"{ticks_per_sec:.2f} tps | {avg_step_time*1000:.2f} ms/tick")

            last_time = now

    total_time = time.perf_counter() - start_time
    avg_tick_time = total_time / SIMULATION_STEPS
    print("⏱️ Всего времени:", f"{total_time:.2f}s")
    print("⚡ Средняя скорость:", f"{1/avg_tick_time:.2f} тиков/сек ({avg_tick_time*1000:.2f} мс/тик)")

    # === Сохранение ===
    os.makedirs(SAVES_DIR, exist_ok=True)
    save_path = os.path.join(SAVES_DIR, "simulation_state.json")

    print("💾 Сохранение состояния...")
    world.save(save_path)

    print("✅ Симуляция завершена и сохранена в", save_path)

    # === Проверка загрузки ===
    restored = World.load(save_path)
    print("♻️ Загрузка успешна! Tick:", restored.tick)