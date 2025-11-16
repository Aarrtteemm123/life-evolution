import math
import random
from typing import Optional


class Action:
    DIVIDE = 'DIVIDE'  # деление клетки
    EMIT = 'EMIT'  # выделение вещества
    ABSORB = 'ABSORB'  # поглощение вещества
    MOVE = 'MOVE'  # движение
    HEALS = 'HEALS'  # лечения

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
            self._execute_divide(cell, environment)

        elif self.type == Action.EMIT and self.substance_name:
            self._execute_emit(cell, environment)

        elif self.type == Action.ABSORB and self.substance_name:
            self._execute_absorb(cell, environment)

        elif self.type == Action.MOVE:
            self._execute_move(cell, environment)

        elif self.type == Action.HEALS:
            self._execute_heals(cell)

    def _execute_divide(self, cell: 'Cell', environment: "Environment"):
        new_cell = cell.divide(environment)
        if new_cell:
            environment.add_cell_to_buffer(new_cell)

    def _execute_emit(self, cell: 'Cell', environment: "Environment"):
        cell.emit(self.substance_name, self.power, environment)

    def _execute_absorb(self, cell: 'Cell', environment: "Environment"):
        x, y = cell.get_int_position()
        substance = environment.grid.get_substance(x, y, self.substance_name)
        cell.absorb(substance)

    def _execute_heals(self, cell: 'Cell'):
        cell.heals(self.power)

    def _execute_move(self, cell: 'Cell', environment: "Environment"):
        """Обработка различных режимов движения."""
        if not self.move_mode:
            return

        x, y = cell.get_int_position()

        if self.move_mode == Action.MOVE_RANDOM or not self.substance_name:
            dx = random.uniform(-1, 1)
            dy = random.uniform(-1, 1)

        else:
            # получаем концентрацию в текущей позиции для сравнения
            current_concentration = environment.grid.get_concentration(x, y, self.substance_name)

            # ищем концентрацию вокруг клетки
            best_dir = None
            best_value = None
            vision_radius = 3

            # Проверяем только соседние ячейки (в пределах vision_radius)
            directions = [
                (ix, iy)
                for ix in range(-vision_radius, vision_radius + 1)
                for iy in range(-vision_radius, vision_radius + 1)
                if not (ix == 0 and iy == 0)
            ]

            for (ix, iy) in directions:
                nx, ny = int(x) + ix, int(y) + iy
                # Проверяем границы сетки
                if not (0 <= nx < environment.grid.width and 0 <= ny < environment.grid.height):
                    continue

                val = environment.grid.get_concentration(nx, ny, self.substance_name)

                # Для TOWARD: ищем направление с БОЛЬШЕЙ концентрацией, чем текущая
                if self.move_mode == Action.MOVE_TOWARD:
                    if val > current_concentration:
                        if best_value is None or val > best_value:
                            best_value = val
                            best_dir = (ix, iy)

                # Для AWAY: ищем направление с МЕНЬШЕЙ концентрацией, чем текущая
                elif self.move_mode == Action.MOVE_AWAY:
                    # Если текущая концентрация = 0, ищем направление с минимальной концентрацией
                    if current_concentration == 0:
                        if best_value is None or val < best_value:
                            best_value = val
                            best_dir = (ix, iy)
                    elif val < current_concentration:
                        if best_value is None or val < best_value:
                            best_value = val
                            best_dir = (ix, iy)

                # Для AROUND: сначала находим направление к веществу (как TOWARD)
                elif self.move_mode == Action.MOVE_AROUND:
                    if val > current_concentration:
                        if best_value is None or val > best_value:
                            best_value = val
                            best_dir = (ix, iy)

            # Если не нашли подходящее направление (вещество везде одинаковое или отсутствует)
            if best_dir is None:
                dx = 0
                dy = 0
            else:
                dx, dy = best_dir
                if self.move_mode == Action.MOVE_AROUND:
                    # поворот на 90° против часовой стрелки (перпендикуляр к градиенту)
                    dx, dy = -dy, dx

        # нормализация скорости
        length = math.hypot(dx, dy)
        if length > 0:
            dx = (dx / length) * self.power * 0.1
            dy = (dy / length) * self.power * 0.1
        else:
            # Если длина 0, не двигаемся
            return

        cell.calculate_new_velocity(dx, dy)

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
