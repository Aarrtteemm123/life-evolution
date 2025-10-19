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
        self.energy: float = 10.0
        self.health: float = 10.0
        self.age: int = 0
        self.alive: bool = True

        # --- внутреннее содержимое ---
        self.genes: List[Gene] = []
        self.substances: Dict[str, Substance] = {}  # вещества внутри клетки

        # --- параметры эволюции ---
        self.mutation_rate: float = 0.05

    def update(self, environment: Dict[str, Any]):
        """
        Один шаг симуляции (время, тик).
        Клетка проверяет свои гены и реагирует на среду.
        """
        if not self.alive:
            return

        self.age += 1
        self.energy -= 0.1  # базовое потребление

        # активация генов
        for gene in self.genes:
            gene.try_activate(self, environment)

        # обновление веществ
        for substance in self.substances.values():
            substance.update()

        # смерть, если энергия или здоровье на нуле
        if self.energy <= 0 or self.health <= 0:
            self.die()

    def absorb(self, substance: Substance):
        """Поглощает вещество (например, из среды)."""
        existing = self.substances.get(substance.name)
        if existing:
            existing.concentration += substance.concentration
        else:
            self.substances[substance.name] = substance.clone()
        self.energy += substance.energy * substance.concentration

    def emit(self, substance_name: str, amount: float, environment: Dict[str, Any]):
        """Выделяет вещество в окружающую среду."""
        sub = self.substances.get(substance_name)
        if not sub or sub.concentration < amount:
            return
        sub.concentration -= amount
        environment.setdefault("emitted", []).append(
            Substance(
                name=sub.name,
                type_=sub.type,
                concentration=amount,
                energy=sub.energy,
            )
        )
        self.energy -= amount * 0.2

    def move(self, dx: float, dy: float):
        """Перемещение клетки (упрощенно)."""
        self.position = (self.position[0] + dx, self.position[1] + dy)
        self.energy -= 0.1 * (abs(dx) + abs(dy))

    def divide(self) -> 'Cell':
        """Создает копию клетки с возможной мутацией."""
        from copy import deepcopy
        new_cell = deepcopy(self)
        new_cell.age = 0
        new_cell.mutate()
        new_cell.position = (self.position[0] + 1, self.position[1])  # смещение
        self.energy /= 2
        new_cell.energy = self.energy
        return new_cell

    def transfer_energy(self, neighbor: 'Cell', amount: float):
        """Передача энергии соседней клетке."""
        if self.energy < amount:
            return
        self.energy -= amount
        neighbor.energy += amount

    def mutate(self):
        """Мутация всей клетки (генов и параметров)."""
        for gene in self.genes:
            gene.mutate()
        # вероятность появления нового гена
        # (можно позже добавить фабрику генов)
        if self.genes and self.mutation_rate > 0.01:
            self.mutation_rate *= 1 + (0.1 * (0.5 - self.mutation_rate))

    def die(self):
        """Прекращает жизнь клетки."""
        self.alive = False
        self.health = 0
        self.energy = 0

    def is_alive(self) -> bool:
        return self.alive

    def clone(self) -> 'Cell':
        """Создаёт копию без мутации."""
        from copy import deepcopy
        return deepcopy(self)

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

        from models.gene import Gene
        from models.substance import Substance
        cell.genes = [Gene.from_dict(g) for g in data.get("genes", [])]
        cell.substances = {s["name"]: Substance.from_dict(s) for s in data.get("substances", [])}
        return cell

    def __repr__(self):
        return (
            f"Cell(pos={self.position}, E={self.energy:.2f}, H={self.health:.2f}, "
            f"genes={len(self.genes)}, subs={len(self.substances)}, age={self.age})"
        )
