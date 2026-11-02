"""Motor de simulación de la Máquina de Turing de una cinta."""

from .models import InstantaneousDescription, Outcome, SimulationResult
from .tape import Tape

DEFAULT_MAX_STEPS = 10_000


def _describe(step, state, cache, tape):
    symbols, head = tape.snapshot()
    return InstantaneousDescription(step, state, cache, symbols, head)


def simulate(machine, word, max_steps=DEFAULT_MAX_STEPS):
    if max_steps < 0:
        raise ValueError("max_steps no puede ser negativo")

    invalid = machine.invalid_symbols(word)
    if invalid:
        return SimulationResult(
            word,
            Outcome.INVALID_INPUT,
            message=f"Símbolos fuera del alfabeto de entrada: {', '.join(invalid)}",
        )

    tape = Tape(word, machine.blank)
    state, cache = machine.initial_state, machine.blank
    ids = [_describe(0, state, cache, tape)]
    step = 0

    while True:
        # La máquina se detiene en cuanto entra en un estado de aceptación.
        if machine.is_accepting(state):
            outcome = Outcome.ACCEPTED
            message = f"Se alcanzó el estado de aceptación {state}"
            break

        symbol = tape.read()
        transition = machine.get_transition(state, cache, symbol)
        if transition is None:
            outcome = Outcome.REJECTED
            message = (
                f"No existe δ([{state}, {cache}], {symbol}) y {state} "
                "no es un estado de aceptación"
            )
            break

        # El límite se revisa después de buscar la transición, para que una
        # máquina que se detiene justo en el paso max_steps no se marque como límite.
        if step >= max_steps:
            outcome = Outcome.STEP_LIMIT
            message = f"Se alcanzó el límite de {max_steps} pasos sin que la máquina se detuviera"
            break

        tape.write(transition.write_symbol)
        tape.move(transition.move)
        state, cache = transition.next_state, transition.write_cache
        step += 1
        ids.append(_describe(step, state, cache, tape))

    return SimulationResult(word, outcome, ids, tape.content(), message)


def simulate_all(machine, max_steps=DEFAULT_MAX_STEPS):
    return [simulate(machine, word, max_steps) for word in machine.inputs]
