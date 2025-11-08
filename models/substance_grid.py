from typing import Dict, List, Tuple

from models.substance import Substance
from config import SUBSTANCE_DIFFUSION_RATE


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

    def update(self):
        """Обновляет вещества и удаляет неактивные (с нулевой концентрацией)."""
        # Рассеивание происходит только если включено в конфигурации
        if SUBSTANCE_DIFFUSION_RATE > 0:
            self.diffuse()
        for pos in list(self.grid.keys()):
            new_subs = []
            for sub in self.grid[pos]:
                sub.update()
                if sub.is_active():
                    new_subs.append(sub)

            if new_subs:
                self.grid[pos] = new_subs
            else:
                del self.grid[pos]


    def diffuse(self, rate: float = None):
        """
        Простое рассеивание веществ по соседним ячейкам.
        Рассеивает вещества между соседними ячейками без потери общей концентрации.
        """
        if rate is None:
            rate = SUBSTANCE_DIFFUSION_RATE
        
        if rate <= 0:
            return
        
        new_grid: Dict[Tuple[int, int], List[Substance]] = {}

        for (x, y), subs in self.grid.items():
            for sub in subs:
                if sub.concentration < 0.01:
                    continue

                # используем исходную концентрацию для расчёта долей
                original_concentration = sub.concentration

                # часть концентрации остаётся на месте
                main_part = original_concentration * (1 - rate)
                
                # оставшаяся часть распределяется по соседям (равномерно на 4 стороны)
                spread_per_neighbor = (original_concentration * rate) / 4
                neighbor_count = 0
                
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        neighbor_count += 1
                        new_grid.setdefault((nx, ny), []).append(
                            Substance(sub.name, sub.type, spread_per_neighbor, sub.energy, sub.volatility)
                        )

                # Если не все соседи доступны (на границе), оставшаяся часть возвращается в текущую ячейку
                if neighbor_count < 4:
                    main_part += spread_per_neighbor * (4 - neighbor_count)
                
                # вернуть основную часть вещества в текущую клетку
                if main_part > 0.01:
                    new_grid.setdefault((x, y), []).append(
                        Substance(sub.name, sub.type, main_part, sub.energy, sub.volatility)
                    )

        # слияние ячеек, чтобы объединить одинаковые вещества
        merged: Dict[Tuple[int, int], List[Substance]] = {}
        for pos, subs in new_grid.items():
            by_name: Dict[str, Substance] = {}
            for s in subs:
                if s.name in by_name:
                    by_name[s.name].concentration += s.concentration
                else:
                    by_name[s.name] = s.clone()
            merged[pos] = list(by_name.values())

        self.grid = merged


    def get_substances(self, x: int, y: int) -> List[Substance]:
        """Возвращает список веществ в ячейке (может быть пустым)."""
        return self.grid.get((x, y), [])

    def get_substance(self, x: int, y: int, substance_name: str) -> Substance | None:
        for sub in self.grid.get((x, y), []):
            if sub.name == substance_name:
                return sub
        return None

    def set_substances(self, x: int, y: int, substances: List[Substance]):
        """Полностью заменяет содержимое ячейки."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        self.grid[(x, y)] = substances

    def add_substance(self, x: int, y: int, substance: Substance):
        """Добавляет вещество в ячейку (если есть — смешивает)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        cell = self.grid.setdefault((x, y), []) # get cell by (x, y) or create default empty list
        for existing in cell:
            if existing.name == substance.name:
                existing.concentration += substance.concentration
                return

        # если такого вещества нет — добавить новое
        cell.append(substance.clone())

    def get_concentration(self, x: int, y: int, name: str) -> float:
        """Возвращает концентрацию указанного вещества в ячейке."""
        for sub in self.grid.get((x, y), []):
            if sub.name == name:
                return sub.concentration
        return 0.0

    def to_dict(self):
        all_subs = []
        for (x, y), subs in self.grid.items():
            for s in subs:
                d = s.to_dict()
                d["x"], d["y"] = x, y
                all_subs.append(d)
        return {"width": self.width, "height": self.height, "substances": all_subs}

    @classmethod
    def from_dict(cls, data):
        grid = cls(data["width"], data["height"])
        for sub in data["substances"]:
            grid.add_substance(sub["x"], sub["y"], Substance.from_dict(sub))
        return grid

    def __repr__(self):
        active_cells = len(self.grid)
        total_subs = sum(len(v) for v in self.grid.values())
        return f"SubstanceGrid({self.width}x{self.height}, cells={active_cells}, substances={total_subs})"
