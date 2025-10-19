import json
from typing import List

from models.cell import Cell
from models.enviroment import Environment
from models.substance_grid import SubstanceGrid


class World:
    """Мир симуляции: управляет временем и средой."""
    def __init__(self, width: int, height: int):
        self.env = Environment(width, height)
        self.tick: int = 0

    def update(self):
        self.tick += 1
        self.env.update()


    def to_dict(self):
        """Преобразует состояние мира в словарь."""
        return {
            "tick": self.tick,
            "environment": {
                "grid": self.env.grid.to_dict(),
                "cells": [c.to_dict() for c in self.env.cells],
            },
        }

    @classmethod
    def from_dict(cls, data):
        """Создаёт объект мира из словаря."""
        env_data = data.get("environment", {})
        grid_data = env_data.get("grid", {})
        cells_data = env_data.get("cells", [])

        # создаём сам мир и окружение
        world = cls(grid_data["width"], grid_data["height"])
        world.tick = data.get("tick", 0)

        # восстанавливаем сетку и клетки
        world.env.grid = SubstanceGrid.from_dict(grid_data)
        world.env.cells = [Cell.from_dict(c) for c in cells_data]

        return world

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
