from typing import Dict, Any
from trigger import Trigger
from action import Action


class Gene:
    """
    Базовый ген — связывает триггер и действие.
    Если условие триггера выполняется, то активируется действие.
    """

    def __init__(
        self,
        receptor: str,
        trigger: Trigger,
        action: Action,
        efficiency: float = 1.0,
        active: bool = True
    ):
        """
        :param receptor: имя вещества или параметра, на который реагирует ген
        :param trigger: условие активации
        :param action: действие при активации
        :param efficiency: коэффициент силы действия
        :param active: активен ли ген (может быть выключен)
        """
        self.receptor = receptor
        self.trigger = trigger
        self.action = action
        self.efficiency = efficiency
        self.active = active


    def try_activate(self, cell: 'Cell', environment: Dict[str, Any]):
        """Проверяет условие и выполняет действие, если сработал триггер."""
        if not self.active:
            return

        # значение рецептора — может быть из среды или состояния клетки
        value = environment.get(self.receptor)
        if value is None:
            # если нет в среде, пробуем взять из параметров клетки
            value = getattr(cell, self.receptor, None)

        if value is None:
            return

        if self.trigger.check(value):
            self.action.execute(cell, environment)


    def mutate(self, rate: float = 0.05):
        """Простая мутация параметров гена."""
        import random
        if random.random() < rate:
            self.efficiency *= random.uniform(0.9, 1.1)
        if random.random() < rate * 0.2:
            self.active = not self.active
        # мутация вложенных компонентов
        self.trigger.threshold *= random.uniform(0.95, 1.05)
        self.action.power *= random.uniform(0.9, 1.1)

    def clone(self) -> 'Gene':
        """Создаёт копию гена (например, при делении клетки)."""
        return Gene(
            receptor=self.receptor,
            trigger=self.trigger,
            action=self.action.clone(),
            efficiency=self.efficiency,
            active=self.active
        )

    def __repr__(self):
        return (f"Gene(receptor={self.receptor}, {self.trigger}, "
                f"{self.action}, eff={self.efficiency:.2f}, active={self.active})")
