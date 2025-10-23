from typing import Optional


class Action:
    DIVIDE = 'DIVIDE'           # деление клетки
    EMIT = 'EMIT'               # выделение вещества
    ABSORB = 'ABSORB'           # поглощение вещества
    MOVE = 'MOVE'               # движение
    HEALS = 'HEALS'             # лечения

    def __init__(
        self,
        type_: str,
        power: float = 1.0,
        substance_name: Optional[str] = None,
        direction: Optional[tuple] = None
    ):
        """
        :param type_: тип действия
        :param power: сила действия (энергия, объём, дальность)
        :param substance_name: имя вещества (для EMIT/ABSORB)
        """
        self.type = type_
        self.power = power
        self.substance_name = substance_name

    def execute(self, cell: 'Cell', environment: "Environment"):
        """Выполняет действие"""
        if self.type == Action.DIVIDE:
           cell.divide()

        elif self.type == Action.EMIT and self.substance_name:
            cell.emit(self.substance_name, self.power, environment)

        elif self.type == Action.ABSORB and self.substance_name:
            x, y = cell.position
            substance = environment.grid.get_substance(x, y, self.substance_name)
            cell.absorb(substance)

        elif self.type == Action.MOVE:
            pass

        elif self.type == Action.HEALS:
           cell.heals()

    def clone(self) -> 'Action':
        return Action.from_dict(self.to_dict())

    def __repr__(self):
        info = [f"type={self.type}", f"power={self.power:.2f}"]
        if self.substance_name:
            info.append(f"substance={self.substance_name}")
        return f"Action({', '.join(info)})"

    def to_dict(self):
        return {
            "type": self.type,
            "power": self.power,
            "substance_name": self.substance_name,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            type_=data["type"],
            power=data.get("power", 1.0),
            substance_name=data.get("substance_name"),
        )

