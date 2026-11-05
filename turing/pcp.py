
from dataclasses import dataclass

EPSILON = "ε"


@dataclass(frozen=True)
class Domino:
    top: tuple
    bottom: tuple

    def __post_init__(self):
        object.__setattr__(self, "top", tuple(self.top))
        object.__setattr__(self, "bottom", tuple(self.bottom))

    def __str__(self):
        return f"({_join(self.top)}, {_join(self.bottom)})"


@dataclass(frozen=True)
class SequenceCheck:
    indices: tuple
    top: tuple
    bottom: tuple

    @property
    def is_solution(self):
        return bool(self.indices) and self.top == self.bottom


class PCPInstance:
    def __init__(self, dominoes):
        self.dominoes = tuple(dominoes)

    def __len__(self):
        return len(self.dominoes)

    def get(self, index):
        if not 1 <= index <= len(self.dominoes):
            raise ValueError(
                f"Índice de dominó fuera de rango: {index} (hay {len(self.dominoes)})"
            )
        return self.dominoes[index - 1]

    def check(self, indices):
        indices = tuple(indices)
        top, bottom = [], []
        for index in indices:
            domino = self.get(index)
            top.extend(domino.top)
            bottom.extend(domino.bottom)
        return SequenceCheck(indices, tuple(top), tuple(bottom))

    def is_solution(self, indices):
        return self.check(indices).is_solution


def _join(tokens):
    return " ".join(tokens) if tokens else EPSILON
