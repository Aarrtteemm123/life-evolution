import random
from config import ALL_SUBSTANCE_NAMES
from models.action import Action
from models.trigger import Trigger


class Gene:
    """
    Базовый ген — связывает триггер и действие.
    Если условие триггера выполняется, то активируется действие.
    """

    def __init__(
        self,
        receptor: str,
        trigger: Trigger,
        action: Action,
        active: bool = True,
        mutation_rate: float = 0.07
    ):
        """
        :param receptor: имя вещества или параметра, на который реагирует ген
        :param trigger: условие активации
        :param action: действие при активации
        :param active: активен ли ген (может быть выключен)
        """
        self.receptor = receptor
        self.trigger = trigger
        self.action = action
        self.active = active
        self.mutation_rate = mutation_rate


    def try_activate(self, cell: "Cell", environment: "Environment"):
        """Проверяет условие и выполняет действие, если сработал триггер."""
        if not self.active:
            return

        value = None

        # --- 1. Попробуем получить значение вещества из среды ---
        if self.receptor not in ("energy", "health"):
            x, y = cell.get_int_position()
            substance = environment.grid.get_substance(x, y, self.receptor)
            if substance:
                value = substance.concentration

        # --- 2. Если вещество не найдено, пробуем взять из клетки ---
        if value is None:
            value = getattr(cell, self.receptor, None)

        if value is None:
            return

        if self.trigger.check(value):
            self.action.execute(cell, environment)


    def mutate(self):
        """Простая мутация параметров гена."""
        if not self.is_triggered_mutation():
            return None

        if self.is_triggered_mutation():
            self.active = not self.active

        if self.is_triggered_mutation():
            if self.receptor in ("energy", "health"):
                self.trigger.threshold = random.uniform(1, 100.0)
            else:
                self.trigger.threshold = random.uniform(0.1, 10.0)

        if self.is_triggered_mutation():
            self.action.power = random.uniform(0.1, 10.0)

        if self.is_triggered_mutation():
            return Gene.create_random_gene()

        if self.is_triggered_mutation():
            self.action.move_mode = random.choice([
                Action.MOVE_RANDOM,
                Action.MOVE_TOWARD,
                Action.MOVE_AWAY,
                Action.MOVE_AROUND,
                None,
            ])

        if self.is_triggered_mutation():
            self.mutation_rate *= random.choice((1.15, 0.85))
            self.mutation_rate = min(self.mutation_rate, 1.0)

        return None

    def is_triggered_mutation(self):
        return random.random() < self.mutation_rate

    @classmethod
    def create_random_gene(cls) -> 'Gene':
        """Создаёт случайный ген."""
        # 85% генов реагируют на вещества, 15% — на внутренние параметры клетки
        if random.random() < 0.85:
            receptor = random.choice(ALL_SUBSTANCE_NAMES)
        else:
            receptor = random.choice(["energy", "health"])

        if receptor in ("energy", "health"):
            threshold = random.uniform(1, 100.0)
        else:
            threshold = random.uniform(0.1, 10.0)
        mode = random.choice((Trigger.LESS, Trigger.GREATER))
        trigger = Trigger(threshold, mode)

        action_type = random.choice((
            Action.DIVIDE, Action.EMIT, Action.ABSORB,
            Action.MOVE, Action.HEALS
        ))

        if action_type == Action.MOVE:
            move_mode = random.choice([
                Action.MOVE_RANDOM,
                Action.MOVE_TOWARD,
                Action.MOVE_AWAY,
                Action.MOVE_AROUND,
            ])
            substance_name = random.choice(ALL_SUBSTANCE_NAMES)
        else:
            move_mode = None
            substance_name = random.choice(ALL_SUBSTANCE_NAMES)

        action = Action(
            type_=action_type,
            power=random.uniform(0.1, 10.0),
            substance_name=substance_name,
            move_mode=move_mode,
        )

        return Gene(
            receptor=receptor,
            trigger=trigger,
            action=action
        )

    def to_tuple(self) -> tuple:
        """Простой стабильный ключ гена."""
        return (
            self.receptor,
            getattr(self.trigger, "mode", ""),
            round(getattr(self.trigger, "threshold", 0.0), 3),
            getattr(self.action, "type", ""),
            round(getattr(self.action, "power", 0.0), 3),
            getattr(self.action, "substance_name", "") or "",
            getattr(self.action, "move_mode", "") or "",
            self.active,
        )


    def clone(self) -> 'Gene':
        """Создаёт копию без мутации."""
        return Gene.from_dict(self.to_dict())

    def to_dict(self):
        return {
            "receptor": self.receptor,
            "trigger": self.trigger.to_dict(),
            "action": self.action.to_dict(),
            "active": self.active,
            "mutation_rate": self.mutation_rate,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            receptor=data["receptor"],
            trigger=Trigger.from_dict(data["trigger"]),
            action=Action.from_dict(data["action"]),
            active=data.get("active", True),
            mutation_rate=data.get("mutation_rate", 0.07)
        )

    def __repr__(self):
        return (f"Gene(receptor={self.receptor}, {self.trigger}, "
                f"{self.action}, active={self.active})")
