

from dataclasses import dataclass

from .models import MOVES, Outcome
from .simulator import DEFAULT_MAX_STEPS, simulate

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
    dominoes = _move_dominoes(q, r, (t.read_symbol,), t.write_symbol, t.move, gamma, (), blank)
    if t.read_symbol == blank:
        # Leer un blanco a la derecha del contenido: aparece como `#` en la configuración.
        dominoes += _move_dominoes(q, r, (HASH,), t.write_symbol, t.move, gamma, (HASH,), blank)
    return dominoes


def _move_dominoes(q, r, read, write, move, gamma, after, blank):
    if move == "R":
        return [Domino((q, *read), (write, r, *after))]
    if move == "S":
        return [Domino((q, *read), (r, write, *after))]
    dominoes = [Domino((c, q, *read), (r, c, write, *after)) for c in gamma]
    # Cabezal en el primer símbolo: la cinta crece a la izquierda con un blanco nuevo.
    dominoes.append(Domino((q, *read), (r, blank, write, *after)))
    return dominoes


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


def solution_indices(machine, word, instance=None, max_steps=DEFAULT_MAX_STEPS):
    if instance is None:
        instance = build_pcp(machine, word)
    result = simulate(machine, word, max_steps)
    if result.outcome is not Outcome.ACCEPTED:
        return None

    lookup = {}
    for number, domino in enumerate(instance.dominoes, start=1):
        lookup.setdefault(domino, number)

    def index(domino):
        if domino not in lookup:
            raise ValueError(f"La instancia no contiene el dominó {domino}")
        return lookup[domino]

    def copies(tokens):
        return [index(Domino((x,), (x,))) for x in tokens]

    tokens, head = list(word), 0
    indices = [1]
    for before in result.ids[:-1]:
        t = machine.get_transition(before.state, before.cache, before.tape[before.head])
        step, head = _step_indices(t, tokens, head, machine.blank, index, copies)
        indices += step

    final = result.ids[-1]
    return indices + _closing_indices(
        tokens, head, state_token(final.state, final.cache), index, copies
    )


def _step_indices(t, tokens, head, blank, index, copies):
    """Índices de una transición; actualiza `tokens` y devuelve (índices, nuevo cabezal)."""
    q = state_token(t.state, t.read_cache)
    r = state_token(t.next_state, t.write_cache)
    at_edge = head == len(tokens)
    read, after = ((HASH,), (HASH,)) if at_edge else ((t.read_symbol,), ())
    left = tokens[head - 1 : head] if head else []
    domino = _move_dominoes(q, r, read, t.write_symbol, t.move, left, after, blank)[0]

    # Con movimiento L y cabezal a la mitad, el dominó también cubre el símbolo de su izquierda.
    consumed_left = len(left) if t.move == "L" else 0
    indices = copies(tokens[: head - consumed_left])
    indices.append(index(domino))
    if not at_edge:
        indices += copies(tokens[head + 1 :])
        indices.append(index(Domino((HASH,), (HASH,))))

    if at_edge:
        tokens.append(t.write_symbol)
    else:
        tokens[head] = t.write_symbol
    if t.move == "L" and head == 0:
        tokens.insert(0, blank)
    else:
        head += MOVES[t.move]
    return indices, head


def _closing_indices(tokens, head, p, index, copies):
    """Borra un símbolo junto a `p` por ronda hasta dejar `p #` y cierra con `p # #`."""
    tokens = list(tokens)
    hash_copy = index(Domino((HASH,), (HASH,)))
    indices = []
    while tokens:
        if head > 0:
            indices += copies(tokens[: head - 1])
            indices.append(index(Domino((tokens[head - 1], p), (p,))))
            indices += copies(tokens[head:])
            del tokens[head - 1]
            head -= 1
        else:
            indices.append(index(Domino((p, tokens[0]), (p,))))
            indices += copies(tokens[1:])
            del tokens[0]
        indices.append(hash_copy)
    indices.append(index(Domino((p, HASH, HASH), (HASH,))))
    return indices


def _join(tokens):
    return " ".join(tokens) if tokens else EPSILON
