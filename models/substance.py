from config import SUBSTANCES


class Substance:
    ORGANIC = 'ORGANIC'
    INORGANIC = 'INORGANIC'
    TOXIN = 'TOXIN'

    def __init__(
        self,
        name: str,
        type_: str,
        concentration: float,
        energy: float,
        volatility: float = 0.02
    ):
        self.name = name
        self.type = type_
        self.concentration = concentration
        self.energy = energy
        self.volatility = volatility  # 0.0 — стабильное, 0.9 — быстро распадается

    def update(self):
        """Естественное рассеивание."""
        self.concentration *= (1.0 - self.volatility)
        if self.concentration < 0.01:
            self.concentration = 0

    def is_active(self) -> bool:
        return self.concentration > 0

    @staticmethod
    def find_substance(name: str):
        data = SUBSTANCES[name]
        return data

    def clone(self) -> 'Substance':
        """Создаёт копию вещества"""
        return Substance.from_dict(self.to_dict())

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "concentration": self.concentration,
            "energy": self.energy,
            "volatility": self.volatility,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            type_=data["type"],
            concentration=data["concentration"],
            energy=data["energy"],
            volatility=data["volatility"]
        )

    def __repr__(self):
        return (f"Substance(name={self.name}, type={self.type}, "
                f"conc={self.concentration:.3f}, energy={self.energy:.2f}, "
                f"volatility={self.volatility:.3f})")