
from dataclasses import dataclass

EPSILON = "ε"
HASH = "#"


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
    def __init__(self, dominoes, start_index=None):
        self.dominoes = tuple(dominoes)
        self.start_index = start_index

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
        indices = tuple(indices)
        if self.start_index is not None and indices[:1] != (self.start_index,):
            return False
        return self.check(indices).is_solution


def state_token(state, cache):
    """Token que representa el estado efectivo [q, caché] dentro de un dominó."""
    return f"[{state},{cache}]"


def build_pcp(machine, word):
    """Instancia (MPCP) cuya solución es el historial de cómputo de `machine` con `word`.

    Sigue la construcción clásica (Sipser, teorema 5.15). Cada configuración se
    escribe como  X1 ... [q,c] Xi ... Xn #  y el control finito es el par [q, caché].
    Lo que se supone de la máquina:
      - La cinta tiene extremo izquierdo: si el cabezal intentara salirse por la
        izquierda no hay dominó aplicable y el cómputo se detiene ahí.
      - Los blancos a la derecha del contenido no se escriben; se lee `#` en su lugar.
      - No se construyen transiciones desde estados de aceptación, porque el
        simulador se detiene al entrar en uno.
    El dominó 1 es el inicial, por lo que la instancia fija `start_index = 1`.
    """
    invalid = machine.invalid_symbols(word)
    if invalid:
        raise ValueError(f"Símbolos fuera del alfabeto de entrada: {', '.join(invalid)}")
    _check_tokens(machine)

    gamma = list(machine.tape_alphabet)
    start = state_token(machine.initial_state, machine.blank)

    dominoes = [Domino((HASH,), (HASH, start, *word, HASH))]
    dominoes += [Domino((x,), (x,)) for x in gamma]
    dominoes.append(Domino((HASH,), (HASH,)))

    for t in machine.transitions.values():
        if machine.is_accepting(t.state):
            continue
        dominoes += _transition_dominoes(t, gamma, machine.blank)

    accepting = [state_token(q, c) for q, c in _accepting_pairs(machine)]
    for p in accepting:
        for x in gamma:
            dominoes.append(Domino((x, p), (p,)))
            dominoes.append(Domino((p, x), (p,)))
    for p in accepting:
        dominoes.append(Domino((p, HASH, HASH), (HASH,)))

    return PCPInstance(dominoes, start_index=1)


def _transition_dominoes(t, gamma, blank):
    q = state_token(t.state, t.read_cache)
    r = state_token(t.next_state, t.write_cache)
    dominoes = _move_dominoes(q, r, (t.read_symbol,), t.write_symbol, t.move, gamma, ())
    if t.read_symbol == blank:
        # Leer un blanco a la derecha del contenido: aparece como `#` en la configuración.
        dominoes += _move_dominoes(q, r, (HASH,), t.write_symbol, t.move, gamma, (HASH,))
    return dominoes


def _move_dominoes(q, r, read, write, move, gamma, after):
    if move == "R":
        return [Domino((q, *read), (write, r, *after))]
    if move == "S":
        return [Domino((q, *read), (r, write, *after))]
    return [Domino((c, q, *read), (r, c, write, *after)) for c in gamma]


def _accepting_pairs(machine):
    """Pares [q, caché] de aceptación que la máquina puede alcanzar."""
    reachable = {(machine.initial_state, machine.blank)}
    reachable |= {(t.next_state, t.write_cache) for t in machine.transitions.values()}
    return [
        (q, c)
        for q in machine.states
        if machine.is_accepting(q)
        for c in machine.tape_alphabet
        if (q, c) in reachable
    ]


def _check_tokens(machine):
    if HASH in machine.tape_alphabet:
        raise ValueError(f"El símbolo '{HASH}' está reservado como separador de configuraciones")
    tokens = {state_token(q, c) for q in machine.states for c in machine.tape_alphabet}
    clash = sorted(tokens & set(machine.tape_alphabet))
    if clash:
        raise ValueError(f"Símbolos de cinta que chocan con tokens de estado: {', '.join(clash)}")


def _join(tokens):
    return " ".join(tokens) if tokens else EPSILON
