from typing import Dict, List, Tuple
from substance import Substance


class SubstanceGrid:
    """
    Сетка веществ (химическая среда).
    Каждая ячейка хранит список веществ с концентрациями.
    Клетки не "сидят" на этой сетке — они лишь взаимодействуют с ней.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # сетка: (x, y) -> список веществ
        # храним в виде словаря ради гибкости (позже можно заменить на массив)
        self.grid: Dict[Tuple[int, int], List[Substance]] = {}

    # === Доступ к ячейкам ===

    def get_cell(self, x: int, y: int) -> List[Substance]:
        """Возвращает список веществ в ячейке (может быть пустым)."""
        return self.grid.get((x, y), [])

    def set_cell(self, x: int, y: int, substances: List[Substance]):
        """Полностью заменяет содержимое ячейки."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self.grid[(x, y)] = substances

    def add_substance(self, x: int, y: int, substance: Substance):
        """Добавляет вещество в ячейку (если есть — смешивает)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        cell = self.grid.setdefault((x, y), [])
        for existing in cell:
            if existing.name == substance.name:
                existing.concentration += substance.concentration
                existing.energy = (existing.energy + substance.energy) / 2
                return

        # если такого вещества нет — добавить новое
        cell.append(substance.clone())

    def diffuse(self, rate: float = 0.1):
        """
        Простое рассеивание веществ по соседним ячейкам.
        (пока что грубое приближение, без физики)
        """
        new_grid: Dict[Tuple[int, int], List[Substance]] = {}

        for (x, y), subs in self.grid.items():
            for sub in subs:
                if not sub.is_active():
                    continue

                sub.update()

                # часть концентрации остаётся на месте
                main_part = sub.concentration * (1 - rate)
                sub.concentration = main_part

                # оставшаяся часть распределяется по соседям
                spread = sub.concentration * rate / 4
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < self.width and 0 <= ny < self.height):
                        continue
                    new_grid.setdefault((nx, ny), []).append(
                        Substance(sub.name, sub.type, spread, sub.energy)
                    )

                # вернуть обновлённое вещество в текущую клетку
                new_grid.setdefault((x, y), []).append(sub.clone())

        # слияние ячеек, чтобы объединить одинаковые вещества
        merged: Dict[Tuple[int, int], List[Substance]] = {}
        for pos, subs in new_grid.items():
            by_name: Dict[str, Substance] = {}
            for s in subs:
                if s.name in by_name:
                    by_name[s.name].concentration += s.concentration
                    by_name[s.name].energy = (by_name[s.name].energy + s.energy) / 2
                else:
                    by_name[s.name] = s.clone()
            merged[pos] = list(by_name.values())

        self.grid = merged

    def get_concentration(self, x: int, y: int, name: str) -> float:
        """Возвращает концентрацию указанного вещества в ячейке."""
        for sub in self.grid.get((x, y), []):
            if sub.name == name:
                return sub.concentration
        return 0.0

    def __repr__(self):
        active_cells = len(self.grid)
        total_subs = sum(len(v) for v in self.grid.values())
        return f"SubstanceGrid({self.width}x{self.height}, cells={active_cells}, substances={total_subs})"
