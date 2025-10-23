from typing import Dict, List, Tuple

from models.substance import Substance


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


    def get_cell(self, x: int, y: int) -> List[Substance]:
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
