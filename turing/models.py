
from dataclasses import dataclass, field
from enum import Enum

BLANK = "B"
MOVES = {"L": -1, "R": 1, "S": 0}


@dataclass(frozen=True)
class Transition:
    """δ([state, read_cache], read_symbol) = ([next_state, write_cache], write_symbol, move)"""

    state: str
    read_symbol: str
    read_cache: str
    next_state: str
    write_cache: str
    write_symbol: str
    move: str

    @property
    def key(self):
        return (self.state, self.read_cache, self.read_symbol)

    def __str__(self):
        return (
            f"δ([{self.state}, {self.read_cache}], {self.read_symbol}) = "
            f"([{self.next_state}, {self.write_cache}], {self.write_symbol}, {self.move})"
        )


@dataclass
class TuringMachine:
    states: list
    input_alphabet: list
    tape_alphabet: list
    initial_state: str
    accept_states: set
    transitions: dict  # (estado, caché, símbolo leído) -> Transition
    inputs: list = field(default_factory=list)
    blank: str = BLANK

    def get_transition(self, state, cache, symbol):
        return self.transitions.get((state, cache, symbol))

    def is_accepting(self, state):
        return state in self.accept_states

    def invalid_symbols(self, word):
        """Símbolos de la cadena que no pertenecen al alfabeto de entrada."""
        allowed = set(self.input_alphabet)
        return sorted({ch for ch in word if ch not in allowed})


class Outcome(Enum):
    ACCEPTED = "ACEPTADA"
    REJECTED = "RECHAZADA"
    STEP_LIMIT = "DETENIDA POR LÍMITE DE PASOS"
    INVALID_INPUT = "ENTRADA INVÁLIDA"


@dataclass(frozen=True)
class InstantaneousDescription:
    """Fotografía de la máquina en un paso: X1...Xi-1 [q, c] Xi...Xn"""

    step: int
    state: str
    cache: str
    tape: tuple  # porción visible de la cinta
    head: int  # índice del cabezal dentro de `tape`

    def __str__(self):
        left = " ".join(self.tape[: self.head])
        right = " ".join(self.tape[self.head :])
        parts = [p for p in (left, f"[{self.state}, {self.cache}]", right) if p]
        return " ".join(parts)


@dataclass
class SimulationResult:
    input_word: str
    outcome: Outcome
    ids: list = field(default_factory=list)
    final_tape: str = ""
    message: str = ""

    @property
    def steps(self):
        return max(len(self.ids) - 1, 0)
