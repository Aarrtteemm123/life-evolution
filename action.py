from typing import Optional, Dict, Any


class Action:
    DIVIDE = 'DIVIDE'           # деление клетки
    EMIT = 'EMIT'               # выделение вещества
    ABSORB = 'ABSORB'           # поглощение вещества
    TRANSFER = 'TRANSFER'       # передача энергии соседним
    MOVE = 'MOVE'               # движение

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
        :param direction: направление (dx, dy) для движения
        """
        self.type = type_
        self.power = power
        self.substance_name = substance_name
        self.direction = direction or (0, 0)

    # === Выполнение действия ===
    def execute(self, cell: 'Cell', environment: Dict[str, Any]):
        """
        Выполняет действие.
        В данной версии environment — это просто словарь.
        В будущем тут будет ссылка на объект World.
        """
        if self.type == Action.DIVIDE:
           pass

        elif self.type == Action.EMIT and self.substance_name:
            pass

        elif self.type == Action.ABSORB and self.substance_name:
           pass

        elif self.type == Action.TRANSFER:
            pass

        elif self.type == Action.MOVE:
           pass

    def clone(self) -> 'Action':
        return Action(
            type_=self.type,
            power=self.power,
            substance_name=self.substance_name,
            direction=self.direction
        )

    def __repr__(self):
        info = [f"type={self.type}", f"power={self.power:.2f}"]
        if self.substance_name:
            info.append(f"substance={self.substance_name}")
        if self.direction != (0, 0):
            info.append(f"dir={self.direction}")
        return f"Action({', '.join(info)})"
