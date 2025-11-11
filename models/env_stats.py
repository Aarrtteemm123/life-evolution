import statistics
from collections import defaultdict, Counter
from typing import Dict

from config import CELLS_LIMIT


class EnvStats:
    """Хранит и обновляет статистику по состоянию окружения."""

    def __init__(self):
        self.cells_total = 0
        self.cells_limit = CELLS_LIMIT
        self.avg_energy = 0.0
        self.avg_health = 0.0
        self.avg_age = 0.0
        self.avg_genes = 0.0
        self.avg_active_genes = 0.0
        self.top_cells = []
        self.total_unique_substances = 0
        self.total_substances_by_type: Dict[str, int] = {}
        self.total_substances_concentration_by_type: Dict[str, float] = {}

    def update(self, env: "Environment"):
        """Обновляет статистику на основе текущего состояния окружения."""
        cells = env.cells
        grid = env.grid

        self.cells_total = len(cells)

        # === 1. Клетки ===
        alive_cells = [c for c in cells if c.alive]
        if alive_cells:
            self.avg_energy = statistics.fmean(c.energy for c in alive_cells)
            self.avg_health = statistics.fmean(c.health for c in alive_cells)
            self.avg_age = statistics.fmean(c.age for c in alive_cells)
            self.avg_genes = statistics.fmean(len(c.genes) for c in alive_cells)
            self.avg_active_genes = statistics.fmean(
                sum(1 for g in c.genes if g.active) for c in alive_cells
            )
        else:
            self.avg_energy = self.avg_health = self.avg_age = self.avg_genes = 0.0

        gene_counter = Counter(c.color_hex for c in alive_cells)
        self.top_cells = [{"key": k, "count": v} for k, v in gene_counter.most_common(5)]

        # === 2. Вещества ===
        # Считаем уникальные вещества по имени и типу
        unique_substances = {}  # key=(name, type) → total_concentration

        for substances in grid.grid.values():
            for s in substances:
                key = (s.name, s.type)
                unique_substances[key] = unique_substances.get(key, 0.0) + s.concentration

        # Общее количество уникальных веществ
        self.total_unique_substances = len(unique_substances)

        # Группировка по типам
        by_type_count = defaultdict(int)
        by_type_conc = defaultdict(float)

        for (_, t), total_conc in unique_substances.items():
            by_type_count[t] += 1
            by_type_conc[t] += total_conc

        # Гарантируем наличие всех категорий
        all_types = ["ORGANIC", "INORGANIC", "TOXIN"]
        self.total_substances_by_type = {t: by_type_count.get(t, 0) for t in all_types}
        self.total_substances_concentration_by_type = {
            t: round(by_type_conc.get(t, 0.0), 3) for t in all_types
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvStats":
        """Создаёт объект статистики из словаря (например, при загрузке мира)."""
        obj = cls()
        obj.cells_total = data.get("cells_total", 0)
        obj.cells_limit = data.get("cells_limit", 0)
        obj.avg_energy = data.get("avg_energy", 0.0)
        obj.avg_health = data.get("avg_health", 0.0)
        obj.avg_age = data.get("avg_age", 0.0)
        obj.avg_genes = data.get("avg_genes", 0.0)
        obj.avg_active_genes = data.get("avg_active_genes", 0.0)
        obj.top_cells = data.get("top_cells", [])
        obj.total_unique_substances = data.get("substances_total", 0)
        obj.total_substances_by_type = data.get(
            "substances_by_type", {}
        )
        obj.total_substances_concentration_by_type = data.get(
            "substances_concentration_by_type", {}
        )
        return obj

    def to_dict(self):
        return {
            "cells_total": self.cells_total,
            "cells_limit": self.cells_limit,
            "avg_energy": self.avg_energy,
            "avg_health": self.avg_health,
            "avg_age": self.avg_age,
            "avg_genes": self.avg_genes,
            "avg_active_genes": self.avg_active_genes,
            "top_cells": self.top_cells,
            "total_unique_substances": self.total_unique_substances,
            "substances_by_type": self.total_substances_by_type,
            "substances_concentration_by_type": self.total_substances_concentration_by_type,
        }

    def __repr__(self):
        return (
            f"WorldStats(cells={self.cells_total}, "
            f"E={self.avg_energy:.2f}, H={self.avg_health:.2f}, "
            f"age={self.avg_age:.1f}, genes={self.avg_genes:.1f}, "
            f"avg_active_genes={self.avg_active_genes:.1f}, "
            f"top_cells={self.top_cells}, "
            f"total_unique_substances={self.total_unique_substances}),"
            f"total_substances_by_type={self.total_substances_by_type}),"
            f"total_substances_concentration_by_type={self.total_substances_concentration_by_type}),"
        )
