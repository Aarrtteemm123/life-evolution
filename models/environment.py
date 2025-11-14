import math
import random
from typing import List
from models.cell import Cell
from models.env_stats import EnvStats
from models.substance_grid import SubstanceGrid
from models.substance import Substance
from config import CELL_RADIUS, CELL_REPULSION_FORCE, ORGANIC_TYPES, ORGANIC_SPAWN_PROBABILITY_PER_CELL_PER_TICK

class Environment:
    """Среда мира: хранит вещества, клетки и API для взаимодействия."""

    def __init__(self, width: int, height: int):
        self.grid = SubstanceGrid(width, height)
        self.cells: List[Cell] = []
        self.buffer_cells: List[Cell] = []
        self.env_stats = EnvStats()

    def add_cell_to_buffer(self, cell: Cell):
        self.buffer_cells.append(cell)

    def load_from_buffer(self):
        self.cells.extend(self.buffer_cells)
        self.buffer_cells = []

    def remove_cell(self, cell: Cell):
        """Удаляет мёртвую клетку из мира."""
        if cell in self.cells:
            self.cells.remove(cell)

    def add_substance(self, x: int, y: int, substance):
        """Добавляет вещество в сетку."""
        self.grid.add_substance(x, y, substance)

    def spawn_random_organic(self):
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                if random.random() < ORGANIC_SPAWN_PROBABILITY_PER_CELL_PER_TICK:
                    # Выбираем случайный тип органики
                    org_data = random.choice(ORGANIC_TYPES)
                    organic_name = org_data["name"]
                    organic_energy = org_data["energy"]
                    
                    # Создаём органическое вещество с концентрацией 10.0 и volatility = 0 (не распадается)
                    organic = Substance(
                        name=organic_name,
                        type_=Substance.ORGANIC,
                        concentration=10.0,
                        energy=organic_energy,
                    )
                    
                    # Добавляем в ячейку
                    self.add_substance(x, y, organic)

    def update_sub_grid(self):
        self.grid.update()

    def update_env_stats(self):
        self.env_stats.update(self)

    def apply_physics(self):
        if len(self.cells) < 2:
            return

        min_distance = 1.8 * CELL_RADIUS  # минимальное расстояние между центрами клеток

        # Проходим по всем парам клеток
        for i in range(len(self.cells)):
            cell1 = self.cells[i]

            for j in range(i + 1, len(self.cells)):
                cell2 = self.cells[j]

                # Вычисляем расстояние между клетками
                dx = cell1.position[0] - cell2.position[0]
                dy = cell1.position[1] - cell2.position[1]
                distance = math.hypot(dx, dy)

                # Если клетки слишком близко или перекрываются
                if min_distance > distance > 0:
                    # Сила отталкивания пропорциональна степени перекрытия
                    overlap = min_distance - distance
                    force = overlap * CELL_REPULSION_FORCE

                    # Нормализуем направление (единичный вектор)
                    if distance > 0:
                        nx = dx / distance
                        ny = dy / distance
                    else:
                        # Если клетки точно в одной точке - случайное направление
                        angle = math.pi * 2 * (i % 8) / 8
                        nx = math.cos(angle)
                        ny = math.sin(angle)

                    # Применяем силу к обеим клеткам (в противоположных направлениях)
                    # Учитываем энергию клеток: более энергичные клетки меньше смещаются
                    weight1 = 1.0 / (1.0 + cell1.energy / 100.0)
                    weight2 = 1.0 / (1.0 + cell2.energy / 100.0)

                    # Смещение первой клетки
                    offset1_x = nx * force * weight2
                    offset1_y = ny * force * weight2
                    new_x1 = cell1.position[0] + offset1_x
                    new_y1 = cell1.position[1] + offset1_y

                    # Смещение второй клетки (в противоположную сторону)
                    offset2_x = -nx * force * weight1
                    offset2_y = -ny * force * weight1
                    new_x2 = cell2.position[0] + offset2_x
                    new_y2 = cell2.position[1] + offset2_y

                    # Ограничиваем границами мира
                    max_x = self.grid.width - 0.5
                    max_y = self.grid.height - 0.5
                    new_x1 = max(0.0, min(max_x, new_x1))
                    new_y1 = max(0.0, min(max_y, new_y1))
                    new_x2 = max(0.0, min(max_x, new_x2))
                    new_y2 = max(0.0, min(max_y, new_y2))

                    # Применяем новые позиции
                    cell1.position = (new_x1, new_y1)
                    cell2.position = (new_x2, new_y2)


    def update_cells(self):
        for cell in self.cells:
            if cell.alive:
                cell.update(self)

        self.load_from_buffer()
        self.cells = [c for c in self.cells if c.alive]

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
