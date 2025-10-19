class Trigger:
    LESS = 'LESS'
    GREATER = 'GREATER'
    EQUAL = 'EQUAL'

    def __init__(self, threshold: float, mode: str = LESS):
        self.threshold = threshold
        self.mode = mode

    def check(self, value: float) -> bool:
        if self.mode == Trigger.LESS:
            return value < self.threshold
        elif self.mode == Trigger.GREATER:
            return value > self.threshold
        elif self.mode == Trigger.EQUAL:
            return abs(value - self.threshold) < 1e-4
        return False

    def to_dict(self):
        return {"threshold": self.threshold, "mode": self.mode}

    @classmethod
    def from_dict(cls, data):
        return cls(threshold=data["threshold"], mode=data["mode"])

    def __repr__(self):
        return f"Trigger(threshold={self.threshold}, mode={self.mode})"

