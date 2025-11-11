import hashlib
import math
import random
from typing import List

from config import ORGANIC_TYPES, CELLS_LIMIT, CELL_RADIUS
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
        genes: List["Gene"] | None = None,
        color_hex: str | None = None,
    ):
        # --- базовые параметры ---
        self.position = position
        self.energy = energy
        self.health = health
        self.age = age
        self.alive = alive

        # --- генетическая информация ---
        self.genes: List[Gene] = genes or []

        self.color_hex = color_hex
        if not color_hex:
            self.update_color()

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

    def move(self, dx: float, dy: float, environment: "Environment"):
        """Перемещение клетки с ограничением в пределах мира."""
        new_x = self.position[0] + dx
        new_y = self.position[1] + dy

        # клэмп по границам сетки
        max_x = environment.grid.width
        max_y = environment.grid.height
        if new_x < 0:
            new_x = CELL_RADIUS
        elif new_x > max_x:
            new_x = max_x - CELL_RADIUS
        if new_y < 0:
            new_y = CELL_RADIUS
        elif new_y > max_y:
            new_y = max_y - CELL_RADIUS

        self.position = (new_x, new_y)
        self.energy -= 0.1 * math.hypot(dx, dy)

    def divide(self, environment: "Environment"):
        """Создает копию клетки с возможной мутацией."""
        if self.energy < 0.1 or (len(environment.cells) + len(environment.buffer_cells) > CELLS_LIMIT):
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
        mutated = new_cell.mutate()
        if mutated:
            new_cell.update_color()

        return new_cell

    def mutate(self):
        """Мутация всей клетки (генов и параметров)."""
        changed = False
        new_genes = []
        for gene in self.genes:
            before = gene.to_dict()
            created = gene.mutate()
            if created:
                new_genes.append(created)
                changed = True
            elif gene.to_dict() != before:
                changed = True

        if new_genes:
            self.genes.extend(new_genes)
            changed = True

        return changed

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

    def get_genes_signature(self) -> str:
        """Короткая сигнатура: отсортированные ключи генов в строку."""
        parts = [g.to_tuple() for g in self.genes]
        parts.sort()
        return "|".join(":".join(map(str, p)) for p in parts)

    def update_color(self):
        sig = self.get_genes_signature().encode("utf-8")
        digest = hashlib.sha1(sig, usedforsecurity=False).digest()  # 20 байт

        r = digest[0] ^ digest[3] ^ digest[6] ^ digest[9] ^ digest[12] ^ digest[15] ^ digest[18]
        g = digest[1] ^ digest[4] ^ digest[7] ^ digest[10] ^ digest[13] ^ digest[16] ^ digest[19]
        b = digest[2] ^ digest[5] ^ digest[8] ^ digest[11] ^ digest[14] ^ digest[17]

        # Немного «поднять» яркость, чтобы цвет не был слишком тёмным.
        # Простая арифметика, без сложной колористики: # 64..191

        r = min(255, 100 + (r // 2))
        g = min(255, 100 + (g // 2))
        b = min(255, 100 + (b // 2))

        self.color_hex = f"#{r:02X}{g:02X}{b:02X}"

    def clone(self) -> 'Cell':
        """Создаёт копию без мутации."""
        return Cell.from_dict(self.to_dict())

    def to_dict(self):
        return {
            "position": self.position,
            "energy": self.energy,
            "health": self.health,
            "age": self.age,
            "color_hex": self.color_hex,
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
        cell.color_hex = data["color_hex"]
        return cell

    def __repr__(self):
        return (
            f"Cell(pos={self.position}, E={self.energy:.2f}, H={self.health:.2f}, "
            f"genes={len(self.genes)}, age={self.age}, "
            f"color_hex={self.color_hex})"
        )
