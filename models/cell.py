import math
from typing import List, Dict, Any

from models.gene import Gene
from models.substance import Substance


class Cell:
    """
    Базовая клетка — минимальный живой агент в симуляции.
    Хранит гены, вещества, энергию, здоровье и позицию.
    """

    def __init__(self, position=(0, 0)):
        # --- базовые параметры ---
        self.position = position
        self.energy: float = 100.0
        self.health: float = 100.0
        self.age: int = 0
        self.alive: bool = True

        # --- внутреннее содержимое ---
        self.genes: List[Gene] = []
        self.substances: Dict[str, Substance] = {}  # вещества внутри клетки

    def update(self, environment: "Environment"):
        """
        Один шаг симуляции (время, тик).
        Клетка проверяет свои гены и реагирует на среду.
        """
        if not self.alive:
            return

        self.age += 1
        self.energy -= 0.1  # базовое потребление

        if self.energy <= 0:
            self.health -= 1

        # активация генов
        for gene in self.genes:
            gene.try_activate(self, environment)

        # смерть, если энергия или здоровье на нуле
        if self.health <= 0:
            self.die()

    def absorb(self, substance: Substance):
        """Поглощает вещество"""
        existing = self.substances.get(substance.name)
        if existing:
            existing.concentration += substance.concentration
        else:
            self.substances[substance.name] = substance.clone()

        substance.concentration = 0

    def emit(self, substance_name: str, amount: float, environment: Dict[str, Any]):
        """Выделяет вещество в окружающую среду."""
        sub = self.substances.get(substance_name)
        if not sub:
            return
        if sub.concentration < amount:
            amount = sub.concentration

        if amount * sub.energy > self.energy:
            amount = self.energy / sub.energy

        self.energy -= amount * sub.energy

        sub.concentration -= amount
        environment.setdefault("emitted", []).append(
            Substance(
                name=sub.name,
                type_=sub.type,
                concentration=amount,
                energy=sub.energy,
            )
        )

    def move(self, dx: float, dy: float):
        """Перемещение клетки (упрощенно)."""
        self.position = (self.position[0] + dx, self.position[1] + dy)
        self.energy -= 0.1 * math.hypot(dx, dy)

    def divide(self) -> 'Cell':
        """Создает копию клетки с возможной мутацией."""
        new_cell = self.clone()
        new_cell.age = 0
        self.energy /= 2
        new_cell.energy /= 2
        new_cell.mutate()
        return new_cell

    def transfer_energy(self, neighbor: 'Cell', amount: float):
        """Передача энергии соседней клетке."""
        if self.energy < amount:
            amount = self.energy
        self.energy -= amount
        neighbor.energy += amount

    def mutate(self):
        """Мутация всей клетки (генов и параметров)."""
        new_genes = []
        for gene in self.genes:
            new_gene = gene.mutate()
            if new_gene:
                new_genes.append(new_gene)
        self.genes.extend(new_genes)

    def die(self):
        """Прекращает жизнь клетки."""
        self.alive = False
        self.health = 0
        self.energy = 0

    def heals(self):
        if self.energy < 1 or self.health > 100:
            return
        self.energy -= 1
        self.health += 1

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
            "substances": [s.to_dict() for s in self.substances.values()]
        }

    @classmethod
    def from_dict(cls, data):
        cell = cls(position=tuple(data["position"]))
        cell.energy = data["energy"]
        cell.health = data["health"]
        cell.age = data["age"]
        cell.genes = [Gene.from_dict(g) for g in data.get("genes", [])]
        cell.substances = {s["name"]: Substance.from_dict(s) for s in data.get("substances", [])}
        return cell

    def __repr__(self):
        return (
            f"Cell(pos={self.position}, E={self.energy:.2f}, H={self.health:.2f}, "
            f"genes={len(self.genes)}, subs={len(self.substances)}, age={self.age})"
        )
