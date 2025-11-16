import hashlib
import math
import random
from typing import List

from config import ORGANIC_TYPES, CELLS_LIMIT, CELL_RADIUS, FRICTION, MAX_VELOCITY, MAX_ACCELERATION, \
    ACCELERATION_FACTOR
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
        mutation_rate: float = 0.1,
        velocity: tuple = (0.0, 0.0),
    ):
        self.position = position
        self.velocity = velocity  # (vx, vy) - скорость
        self.energy = energy
        self.health = health
        self.age = age
        self.alive = alive
        self.genes: List[Gene] = genes or []
        self.color_hex = color_hex
        self.mutation_rate = mutation_rate

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

        # применение скорости для плавного движения
        self.apply_velocity(environment)

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

    def apply_velocity(self, environment: "Environment"):
        """
        Применяет скорость к позиции клетки для плавного движения.
        Также применяет трение для постепенного замедления.
        """
        
        vx, vy = self.velocity
        
        # Применяем трение
        vx *= FRICTION
        vy *= FRICTION
        
        # Ограничиваем максимальную скорость
        speed = math.hypot(vx, vy)
        if speed > MAX_VELOCITY:
            vx = (vx / speed) * MAX_VELOCITY
            vy = (vy / speed) * MAX_VELOCITY
        
        # Обновляем позицию на основе скорости
        new_x = self.position[0] + vx
        new_y = self.position[1] + vy
        
        # Ограничиваем границами мира
        max_x = environment.grid.width
        max_y = environment.grid.height
        if new_x < 0:
            new_x = CELL_RADIUS
            vx = 0  # останавливаем при столкновении со стеной
        elif new_x > max_x:
            new_x = max_x - CELL_RADIUS
            vx = 0
        if new_y < 0:
            new_y = CELL_RADIUS
            vy = 0
        elif new_y > max_y:
            new_y = max_y - CELL_RADIUS
            vy = 0
        
        self.position = (new_x, new_y)
        self.velocity = (vx, vy)
        
        # Энергозатраты пропорциональны скорости
        movement_cost = 0.05 * speed
        self.energy -= movement_cost

    def move(self, dx: float, dy: float):
        """
        Применяет силу к скорости клетки вместо мгновенного перемещения.
        """
        
        # Нормализуем направление если оно не нулевое
        direction_length = math.hypot(dx, dy)
        if direction_length > 0:
            # Нормализуем и умножаем на максимальное ускорение
            norm_dx = (dx / direction_length) * MAX_ACCELERATION
            norm_dy = (dy / direction_length) * MAX_ACCELERATION
            
            # Применяем ускорение к скорости (интерполяция)
            vx, vy = self.velocity
            vx = vx * (1 - ACCELERATION_FACTOR) + norm_dx * ACCELERATION_FACTOR
            vy = vy * (1 - ACCELERATION_FACTOR) + norm_dy * ACCELERATION_FACTOR
            
            self.velocity = (vx, vy)

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
        # Новая клетка начинает с небольшой случайной скорости
        new_cell.velocity = (
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5)
        )

        if self.is_triggered_mutation():
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

    def is_triggered_mutation(self):
        return random.random() < self.mutation_rate

    def die(self, environment: "Environment"):
        """Прекращает жизнь клетки и выделяет вещества в окружающую среду."""

        self.alive = False
        cx, cy = self.get_int_position()
        total_cell_energy = self.energy

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
            "velocity": self.velocity,
            "energy": self.energy,
            "health": self.health,
            "age": self.age,
            "color_hex": self.color_hex,
            "mutation_rate": self.mutation_rate,
            "genes": [g.to_dict() for g in self.genes],
        }

    def get_int_position(self):
        cx, cy = int(self.position[0]), int(self.position[1])
        return cx, cy

    @classmethod
    def from_dict(cls, data):
        cell = cls(position=tuple(data["position"]))
        cell.velocity = tuple(data.get("velocity", (0.0, 0.0)))
        cell.energy = data["energy"]
        cell.health = data["health"]
        cell.age = data["age"]
        cell.genes = [Gene.from_dict(g) for g in data.get("genes", [])]
        cell.color_hex = data["color_hex"]
        cell.mutation_rate = data["mutation_rate"]
        return cell

    def __repr__(self):
        return (
            f"Cell(pos={self.position}, E={self.energy:.2f}, H={self.health:.2f}, "
            f"genes={len(self.genes)}, age={self.age}, velocity={self.velocity})"
            f"color_hex={self.color_hex}), mutation_rate={self.mutation_rate:.2f}"
        )
