import statistics
from collections import Counter
from typing import Dict

class EnvStats:
    """Хранит и обновляет статистику по состоянию окружения."""

    def __init__(self):
        self.cells_total = 0
        self.avg_energy = 0.0
        self.avg_health = 0.0
        self.avg_age = 0.0
        self.avg_genes = 0.0
        self.substances_total = 0
        self.substances_by_type: Dict[str, int] = {}

    def update(self, env: "Environment"):
        """Обновляет статистику на основе текущего состояния окружения."""
        cells = env.cells
        grid = env.grid

        self.cells_total = len(cells)

        # === 1. Клетки ===
        alive_cells = [c for c in cells if c.alive]
        if alive_cells:
            self.avg_energy = statistics.mean(c.energy for c in alive_cells)
            self.avg_health = statistics.mean(c.health for c in alive_cells)
            self.avg_age = statistics.mean(c.age for c in alive_cells)
            self.avg_genes = statistics.mean(len(c.genes) for c in alive_cells)
        else:
            self.avg_energy = self.avg_health = self.avg_age = self.avg_genes = 0.0

        # === 2. Вещества ===
        all_substances = [s.type for subs in grid.grid.values() for s in subs]
        type_counts = Counter(all_substances)
        self.substances_total = sum(type_counts.values())

        # гарантируем наличие всех категорий
        self.substances_by_type = {
            t: type_counts.get(t, 0) for t in ["ORGANIC", "INORGANIC", "TOXIN"]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvStats":
        """Создаёт объект статистики из словаря (например, при загрузке мира)."""
        obj = cls()
        obj.cells_total = data.get("cells_total", 0)
        obj.avg_energy = data.get("avg_energy", 0.0)
        obj.avg_health = data.get("avg_health", 0.0)
        obj.avg_age = data.get("avg_age", 0.0)
        obj.avg_genes = data.get("avg_genes", 0.0)
        obj.substances_total = data.get("substances_total", 0)
        obj.substances_by_type = data.get("substances_by_type", {
            "ORGANIC": 0,
            "INORGANIC": 0,
            "TOXIN": 0
        })
        return obj

    def to_dict(self):
        return {
            "cells_total": self.cells_total,
            "avg_energy": self.avg_energy,
            "avg_health": self.avg_health,
            "avg_age": self.avg_age,
            "avg_genes": self.avg_genes,
            "substances_total": self.substances_total,
            "substances_by_type": self.substances_by_type,
        }

    def __repr__(self):
        return (
            f"WorldStats(cells={self.cells_total}, "
            f"E={self.avg_energy:.2f}, H={self.avg_health:.2f}, "
            f"age={self.avg_age:.1f}, genes={self.avg_genes:.1f}, "
            f"subs={self.substances_total})"
        )
