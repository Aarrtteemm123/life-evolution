import math
import random
from typing import Optional


class Action:
    DIVIDE = 'DIVIDE'           # деление клетки
    EMIT = 'EMIT'               # выделение вещества
    ABSORB = 'ABSORB'           # поглощение вещества
    MOVE = 'MOVE'               # движение
    HEALS = 'HEALS'             # лечения

    MOVE_RANDOM = 'RANDOM'
    MOVE_TOWARD = 'TOWARD'
    MOVE_AWAY = 'AWAY'
    MOVE_AROUND = 'AROUND'

    def __init__(
        self,
        type_: str,
        power: float = 1.0,
        substance_name: Optional[str] = None,
        move_mode: Optional[str] = None
    ):
        """
        :param type_: тип действия
        :param power: сила действия (энергия, объём, дальность)
        :param substance_name: имя вещества (для EMIT/ABSORB)
        :param move_mode: тип движения: TOWARD / AWAY / RANDOM / AROUND
        """
        self.type = type_
        self.power = power
        self.substance_name = substance_name
        self.move_mode = move_mode

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
            self._execute_move(cell, environment)

        elif self.type == Action.HEALS:
           cell.heals(self.power)

    def _execute_move(self, cell: 'Cell', environment: "Environment"):
        """Обработка различных режимов движения."""
        x, y = cell.get_int_position()
        dx, dy = 0.0, 0.0

        if self.move_mode == Action.MOVE_RANDOM or not self.substance_name:
            dx = random.uniform(-1, 1)
            dy = random.uniform(-1, 1)

        else:
            # ищем концентрацию вокруг клетки
            best_dir = None
            best_value = None

            directions = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1), (0, 1),
                (1, -1), (1, 0), (1, 1)
            ]

            for (ix, iy) in directions:
                nx, ny = int(x) + ix, int(y) + iy
                val = environment.grid.get_concentration(nx, ny, self.substance_name)
                if best_value is None or (
                        self.move_mode == Action.MOVE_TOWARD and val > best_value
                ) or (
                        self.move_mode == Action.MOVE_AWAY and val < best_value
                ):
                    best_value = val
                    best_dir = (ix, iy)

            if best_dir:
                dx, dy = best_dir
                if self.move_mode == Action.MOVE_AROUND:
                    # поворот на 90° (перпендикуляр к градиенту)
                    dx, dy = -dy, dx

        # нормализация скорости
        length = math.hypot(dx, dy)
        if length > 0:
            dx = (dx / length) * self.power
            dy = (dy / length) * self.power

        cell.move(dx, dy)

    def clone(self) -> 'Action':
        return Action.from_dict(self.to_dict())

    def __repr__(self):
        info = [f"type={self.type}", f"power={self.power:.2f}"]
        if self.substance_name:
            info.append(f"substance={self.substance_name}")
        if self.move_mode:
            info.append(f"move_mode={self.move_mode}")
        return f"Action({', '.join(info)})"

    def to_dict(self):
        return {
            "type": self.type,
            "power": self.power,
            "substance_name": self.substance_name,
            "move_mode": self.move_mode,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            type_=data["type"],
            power=data.get("power", 1.0),
            substance_name=data.get("substance_name"),
            move_mode=data.get("move_mode"),
        )

