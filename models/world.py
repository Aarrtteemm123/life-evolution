import json
import statistics
from collections import Counter
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
        """Сериализация мира + статистика."""
        env = self.env
        cells = env.cells
        grid = env.grid

        # === 1. Собираем статистику по клеткам ===
        energies = [c.energy for c in cells if c.alive]
        healths = [c.health for c in cells if c.alive]
        ages = [c.age for c in cells if c.alive]
        gene_counts = [len(c.genes) for c in cells if c.alive]

        avg_energy = statistics.mean(energies) if energies else 0
        avg_health = statistics.mean(healths) if healths else 0
        avg_age = statistics.mean(ages) if ages else 0
        avg_genes = statistics.mean(gene_counts) if gene_counts else 0

        # === 2. Статистика по веществам ===
        all_substances = [
            s.type
            for subs in grid.grid.values()
            for s in subs
        ]

        type_counts = Counter(all_substances)
        total_subs = sum(type_counts.values())

        # гарантируем наличие всех трёх категорий
        by_type = {t: type_counts.get(t, 0) for t in ["ORGANIC", "INORGANIC", "TOXIN"]}

        # === 3. Формирование итогового состояния ===
        return {
            "environment": {
                "grid": grid.to_dict(),
                "cells": [c.to_dict() for c in cells],
            },
            "stats": {
                "tick": self.tick,
                "cells_total": len(cells),
                "avg_energy": avg_energy,
                "avg_health": avg_health,
                "avg_age": avg_age,
                "avg_genes": avg_genes,
                "substances_total": total_subs,
                "substances_by_type": by_type,
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
