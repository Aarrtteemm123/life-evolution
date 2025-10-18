import json
from typing import List
from cell import Cell
from substance_grid import SubstanceGrid


class World:
    """Мир симуляции: хранит клетки и сетку веществ."""

    def __init__(self, width: int, height: int):
        self.grid = SubstanceGrid(width, height)
        self.cells: List[Cell] = []
        self.tick: int = 0

    def update(self):
        """Один шаг симуляции."""
        self.tick += 1
        self.grid.diffuse()
        for cell in self.cells:
            env = {"grid": self.grid}
            cell.update(env)


    def to_dict(self):
        return {
            "tick": self.tick,
            "grid": self.grid.to_dict(),
            "cells": [c.to_dict() for c in self.cells]
        }

    @classmethod
    def from_dict(cls, data):
        world = cls(data["grid"]["width"], data["grid"]["height"])
        world.tick = data.get("tick", 0)
        world.grid = SubstanceGrid.from_dict(data["grid"])
        world.cells = [Cell.from_dict(c) for c in data.get("cells", [])]
        return world

    # === Сохранение/загрузка ===

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
