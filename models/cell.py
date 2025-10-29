import math
import random
from typing import List

from config import ORGANIC_TYPES
from models.gene import Gene
from models.substance import Substance


class Cell:
    """
    Базовая клетка — минимальный живой агент в симуляции.
    Хранит гены, вещества, энергию, здоровье и позицию.
    """

    def __init__(
        self,
        position: tuple = (0.0, 0.0),
        energy: float = 100.0,
        health: float = 100.0,
        age: int = 0,
        alive: bool = True,
        genes: List["Gene"] | None = None
    ):
        # --- базовые параметры ---
        self.position = position
        self.energy = energy
        self.health = health
        self.age = age
        self.alive = alive

        # --- генетическая информация ---
        self.genes: List[Gene] = genes or []

    def update(self, environment: "Environment"):
        """
        Один шаг симуляции (время, тик).
        Клетка проверяет свои гены и реагирует на среду.
        """
        if not self.alive:
            return

        self.age += 1
        self.energy -= 0.1  # базовое потребление

        self.apply_toxin_damage(environment)

        # активация генов
        for gene in self.genes:
            gene.try_activate(self, environment)

        # смерть, если энергия или здоровье на нуле
        if self.energy <= 0.01 or self.health <= 0.01:
            self.die(environment)

    def apply_toxin_damage(self, environment: "Environment"):
        """
        Наносит урон клетке, если она находится на ячейке с токсинами.
        Урон пропорционален энергии и концентрации токсина.
        """
        cx, cy = self.get_int_position()
        local_subs = environment.grid.get_substances(cx, cy)

        if not local_subs:
            return

        total_damage = 0.0

        for sub in local_subs:
            if sub.type == Substance.TOXIN and sub.concentration > 0.01:
                # Урон = концентрация × энергия токсина
                # Чем сильнее токсин, тем больше энергия
                damage = sub.energy * sub.concentration
                total_damage += damage

        if total_damage > 0:
            # наносим урон здоровью
            self.health -= total_damage
            if self.health < 0:
                self.health = 0

    def absorb(self, substance: Substance):
        """Поглощает вещество"""
        if not substance or substance.concentration <= 0.01:
            return

        gained_energy = substance.concentration * substance.energy
        self.energy += gained_energy
        # вещество исчезает из среды
        substance.concentration = 0

    def emit(self, substance_name: str, amount: float, environment: "Environment"):
        """Выделяет вещество равномерно во все 8 направлений вокруг клетки."""

        if self.energy <= 0.001 or amount <= 0.001:
            return

        data = Substance.find_substance(substance_name)

        # === Энергозатраты ===
        energy_cost = amount * data["energy"]  # стоимость пропорциональна энергетике вещества
        if self.energy < energy_cost:
            # уменьшаем объём выделения, если энергии не хватает
            amount = self.energy / data["energy"]
            energy_cost = amount * data["energy"]

        self.energy -= energy_cost

        # создаём вещество, которое будет распределено вокруг
        emitted_total = Substance(
            name=substance_name,
            type_=data["type"],
            concentration=amount,
            energy=data["energy"],
        )

        # координата клетки
        cx, cy = self.get_int_position()

        # распределение вещества на все 8 направлений + центр
        directions = [
            (0, 0),  # можно оставить часть вещества под самой клеткой
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]

        spread_concentration = emitted_total.concentration / len(directions)

        for dx, dy in directions:
            x, y = cx + dx, cy + dy
            if not (0 <= x < environment.grid.width and 0 <= y < environment.grid.height):
                continue

            environment.add_substance(
                x, y,
                Substance(
                    name=substance_name,
                    type_=data["type"],
                    concentration=spread_concentration,
                    energy=data["energy"],
                )
            )

    def move(self, dx: float, dy: float):
        """Перемещение клетки (упрощенно)."""
        self.position = (self.position[0] + dx, self.position[1] + dy)
        self.energy -= 0.1 * math.hypot(dx, dy)

    def divide(self):
        """Создает копию клетки с возможной мутацией."""
        if self.energy < 0.1:
            return None
        new_cell = self.clone()
        cell_energy = self.energy / 2
        new_cell.age = 0
        self.energy = cell_energy
        new_cell.energy = cell_energy
        new_cell.position = (
            self.position[0] + random.choice((0.5, -0.5)),
            self.position[1] + random.choice((0.5, -0.5))
        )
        new_cell.mutate()
        return new_cell

    def mutate(self):
        """Мутация всей клетки (генов и параметров)."""
        new_genes = []
        for gene in self.genes:
            new_gene = gene.mutate()
            if new_gene:
                new_genes.append(new_gene)
        self.genes.extend(new_genes)

    def die(self, environment: "Environment"):
        """Прекращает жизнь клетки и выделяет вещества в окружающую среду."""

        self.alive = False
        cx, cy = self.get_int_position()
        total_cell_energy = self.energy + self.health

        # === 2. Конвертировать энергию в органику ===
        if total_cell_energy > 0:
            # случайный тип органики из конфигурации
            org_data = random.choice(ORGANIC_TYPES)
            organic_name = org_data["name"]
            organic_energy = org_data["energy"]

            # расчёт концентрации по энергии
            organic_concentration = total_cell_energy / organic_energy

            # создание органического вещества
            organic = Substance(
                name=organic_name,
                type_=Substance.ORGANIC,
                concentration=organic_concentration,
                energy=organic_energy,
            )

            # добавить всё в текущую ячейку
            environment.add_substance(cx, cy, organic)

        # === 3. Очистка и обнуление клетки ===
        self.energy = 0
        self.health = 0

    def heals(self, amount: float = 1):
        if amount < 1:
            amount = 1

        if self.energy < amount + 5 or self.health > 100:
            return

        self.energy -= amount
        self.health += amount

        if self.health > 100:
            self.health = 100

    def is_alive(self) -> bool:
        return self.alive

    def clone(self) -> 'Cell':
        """Создаёт копию без мутации."""
        return Cell.from_dict(self.to_dict())

    def to_dict(self):
        return {
            "position": self.position,
            "energy": self.energy,
            "health": self.health,
            "age": self.age,
            "genes": [g.to_dict() for g in self.genes],
        }

    def get_int_position(self):
        cx, cy = int(self.position[0]), int(self.position[1])
        return cx, cy

    @classmethod
    def from_dict(cls, data):
        cell = cls(position=tuple(data["position"]))
        cell.energy = data["energy"]
        cell.health = data["health"]
        cell.age = data["age"]
        cell.genes = [Gene.from_dict(g) for g in data.get("genes", [])]
        return cell

    def __repr__(self):
        return (
            f"Cell(pos={self.position}, E={self.energy:.2f}, H={self.health:.2f}, "
            f"genes={len(self.genes)}, age={self.age})"
        )
