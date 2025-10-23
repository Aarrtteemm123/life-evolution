from typing import List
from models.cell import Cell
from models.env_stats import EnvStats
from models.substance_grid import SubstanceGrid

class Environment:
    """Среда мира: хранит вещества, клетки и API для взаимодействия."""

    def __init__(self, width: int, height: int):
        self.grid = SubstanceGrid(width, height)
        self.cells: List[Cell] = []
        self.env_stats = EnvStats()

    def add_cell(self, cell: Cell):
        self.cells.append(cell)

    def remove_cell(self, cell: Cell):
        """Удаляет мёртвую клетку из мира."""
        if cell in self.cells:
            self.cells.remove(cell)

    def add_substance(self, x: int, y: int, substance):
        """Добавляет вещество в сетку."""
        self.grid.add_substance(x, y, substance)

    def update(self):
        """Обновляет вещества и клетки среды."""
        self.grid.update()

        for cell in self.cells:
            if cell.alive:
                cell.update(self)

        self.cells = [c for c in self.cells if c.alive]
        self.env_stats.update(self)

    def to_dict(self) -> dict:
        """Преобразует среду в сериализуемый словарь."""
        return {
            "grid": self.grid.to_dict(),
            "cells": [c.to_dict() for c in self.cells],
            "env_stats": self.env_stats.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Environment":
        """Создаёт среду из сериализованных данных."""
        grid_data = data.get("grid", {})
        cells_data = data.get("cells", [])
        stats_data = data.get("env_stats")

        env = cls(grid_data["width"], grid_data["height"])
        env.grid = SubstanceGrid.from_dict(grid_data)
        env.cells = [Cell.from_dict(c) for c in cells_data]
        env.env_stats = EnvStats.from_dict(stats_data)

        return env
