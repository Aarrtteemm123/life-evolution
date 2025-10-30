import json
import time

from models.environment import Environment


class World:
    """Мир симуляции: управляет временем и средой."""
    def __init__(self, width: int, height: int, tick: int = 0, tick_time_ms: float = 0.0):
        self.env = Environment(width, height)
        self.tick: int = tick
        self.tick_time_ms = tick_time_ms

    def update(self):
        start_time = time.perf_counter()
        self.tick += 1
        self.env.update_cells()
        self.env.update_sub_grid()
        self.env.update_env_stats()
        self.tick_time_ms = (time.perf_counter() - start_time) * 1000

    def to_dict(self):
        """Сериализация мира"""
        from config import SUBSTANCES
        return {
            "tick": self.tick,
            "tick_time_ms": self.tick_time_ms,
            "environment": self.env.to_dict(),
            "substances": SUBSTANCES
        }

    @classmethod
    def from_dict(cls, data):
        """Создаёт объект мира из словаря."""
        env_data = data.get("environment", {})
        grid_data = env_data.get("grid", {})
        import config as _config
        subs = data.get("substances")
        if subs is not None:
            _config.SUBSTANCES = subs
        else:
            from helpers import generate_substances
            generate_substances(_config.SUBSTANCES)

        # создаём сам мир и окружение
        world = cls(
            grid_data["width"],
            grid_data["height"],
            data.get("tick", 0),
            data.get("tick_time_ms", 0)
        )
        world.env = Environment.from_dict(env_data)

        return world

    def save(self, filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
