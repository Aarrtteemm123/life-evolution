import os
import random
import time

from config import CELL_COUNT, WORLD_WIDTH, WORLD_HEIGHT, SIMULATION_STEPS, SAVES_DIR, \
    ORGANIC_TYPES, TOXIN_TYPES, INORGANIC_TYPES, SUBSTANCE_DISTRIBUTION, INCLUDE_BASE_GENES, SUBSTANCES
from models.gene import Gene
from models.trigger import Trigger
from models.action import Action
from models.cell import Cell
from models.substance import Substance
from models.world import World

def generate_substances(container: dict):
    """
    Генерирует глобальный словарь SUBSTANCES из всех категорий веществ.
    Формат:
        {
            "ORGANIC_0": {"type": "ORGANIC", "energy": 1.5},
            "TOXIN_2":   {"type": "TOXIN",   "energy": -4.0},
            "INORGANIC_15": {"type": "INORGANIC", "energy": 0.5},
            ...
        }
    """
    container.clear()

    # === Органика ===
    for data in ORGANIC_TYPES:
        container[data["name"]] = {
            "type": Substance.ORGANIC,
            "energy": data["energy"]
        }

    # === Токсины ===
    for data in TOXIN_TYPES:
        container[data["name"]] = {
            "type": Substance.TOXIN,
            "energy": data["energy"]
        }

    # === Неорганика ===
    for data in INORGANIC_TYPES:
        container[data["name"]] = {
            "type": Substance.INORGANIC,
            "energy": data["energy"]
        }

def random_substance(type_: str = None) -> Substance | None:
    """Создаёт случайное вещество из SUBSTANCES (можно указать тип)."""
    if type_:
        candidates = [n for n, v in SUBSTANCES.items() if v["type"] == type_]
        if not candidates:
            return None
        name = random.choice(candidates)
    else:
        name = random.choice(list(SUBSTANCES.keys()))

    data = SUBSTANCES[name]
    concentration = random.uniform(0.1, 10.0)

    return Substance(
        name=name,
        type_=data["type"],
        concentration=concentration,
        energy=data["energy"],
    )


def base_genes() -> list[Gene]:
    """Создаёт набор базовых генов для ускорения эволюции."""
    genes = []

    # === 1. Двигаться к еде (органике) ===
    # если рядом высокая концентрация органики — двигаться в ту сторону
    for org_type in ORGANIC_TYPES:
        move_to_food = Gene(
            receptor=org_type.get('name'),
            trigger=Trigger(threshold=0.1, mode=Trigger.GREATER),  # мало еды — искать
            action=Action(type_=Action.MOVE_TOWARD, power=1.0),  # движение
        )
        genes.append(move_to_food)

    # === 2. Поглощать еду ===
    for org_type in ORGANIC_TYPES:
        absorb_food = Gene(
            receptor=org_type.get('name'),
            trigger=Trigger(threshold=0.3, mode=Trigger.GREATER),
            action=Action(type_=Action.ABSORB, substance_name=org_type.get('name')),
        )
        genes.append(absorb_food)

    # === 3. Деление клетки при избытке энергии ===
    divide_on_energy = Gene(
        receptor="energy",
        trigger=Trigger(threshold=90, mode=Trigger.GREATER),
        action=Action(type_=Action.DIVIDE),
    )
    genes.append(divide_on_energy)

    return genes


def random_cell(x: int, y: int, include_base_genes=INCLUDE_BASE_GENES) -> Cell:
    """Создаёт клетку с случайным набором генов и начальными параметрами."""
    # Случайное смещение внутри клетки (чтобы не стояли ровно по сетке)
    cell = Cell(position=(x + random.random(), y + random.random()))

    if include_base_genes:
        # === Добавляем базовые гены ===
        for g in base_genes():
            cell.genes.append(g)

    # Количество генов: чаще 2–6, но иногда до 10
    gene_count = random.choices(
        population=range(1, 11),
        weights=[10, 15, 20, 20, 15, 10, 5, 3, 1, 1],  # экспоненциально убывающее
        k=1
    )[0]

    for _ in range(gene_count):
        random_gene = Gene.create_random_gene()
        cell.genes.append(random_gene)

    return cell


def populate_world(world: 'World'):
    """Заполняет мир веществами и клетками."""
    env = world.env
    generate_substances(SUBSTANCES)

    # 1. Заполнение сетки веществ
    for category, count in SUBSTANCE_DISTRIBUTION.items():
        for _ in range(count):
            x = random.randint(0, env.grid.width - 1)
            y = random.randint(0, env.grid.height - 1)
            env.add_substance(x, y, random_substance(category))

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