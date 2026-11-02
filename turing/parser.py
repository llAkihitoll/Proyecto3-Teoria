"""Lectura y validación del archivo YAML que describe la Máquina de Turing."""

import yaml

from .models import BLANK, MOVES, Transition, TuringMachine

REQUIRED_FIELDS = (
    "states",
    "input_alphabet",
    "tape_alphabet",
    "initial_state",
    "accept_states",
    "transitions",
    "inputs",
)
TRANSITION_FIELDS = ("state", "read", "write", "move", "next")


class ConfigError(Exception):
    """Configuración inválida. Agrupa todos los problemas encontrados."""

    def __init__(self, errors):
        self.errors = list(errors) if isinstance(errors, (list, tuple)) else [errors]
        super().__init__(
            "Configuración inválida:\n" + "\n".join(f"  - {e}" for e in self.errors)
        )


def load_machine(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"No se encontró el archivo '{path}'")
    except yaml.YAMLError as e:
        raise ConfigError(f"El archivo '{path}' no es un YAML válido: {e}")
    return parse_machine(data)


def _symbol(value, where, errors):
    """Convierte un escalar YAML a símbolo (str), detectando conversiones peligrosas."""
    if isinstance(value, bool):
        # yes/no/true/false/on/off se convierten en booleanos en YAML
        errors.append(f"{where}: el valor '{value}' se interpretó como booleano; escríbalo entre comillas")
        return None
    if isinstance(value, (int, float)) or isinstance(value, str):
        text = str(value)
        if not text:
            errors.append(f"{where}: no se permiten símbolos vacíos")
            return None
        return text
    errors.append(f"{where}: se esperaba un símbolo, se obtuvo '{value}'")
    return None


def _symbol_list(value, where, errors):
    if not isinstance(value, list):
        errors.append(f"{where}: debe ser una lista")
        return []
    result = []
    for i, item in enumerate(value):
        sym = _symbol(item, f"{where}[{i}]", errors)
        if sym is not None:
            result.append(sym)
    duplicates = sorted({s for s in result if result.count(s) > 1})
    if duplicates:
        errors.append(f"{where}: elementos repetidos {duplicates}")
    return result


def parse_machine(data):
    if not isinstance(data, dict) or "mt" not in data:
        raise ConfigError("El archivo debe tener una clave raíz 'mt'")
    mt = data["mt"]
    if not isinstance(mt, dict):
        raise ConfigError("'mt' debe ser un mapa con la descripción de la máquina")

    missing = [f for f in REQUIRED_FIELDS if f not in mt]
    if missing:
        raise ConfigError([f"Falta el campo obligatorio 'mt.{f}'" for f in missing])

    errors = []
    states = _symbol_list(mt["states"], "states", errors)
    input_alphabet = _symbol_list(mt["input_alphabet"], "input_alphabet", errors)
    tape_alphabet = _symbol_list(mt["tape_alphabet"], "tape_alphabet", errors)
    accept_states = _symbol_list(mt["accept_states"], "accept_states", errors)
    initial_state = _symbol(mt["initial_state"], "initial_state", errors)

    state_set, tape_set = set(states), set(tape_alphabet)

    if not states:
        errors.append("states: debe contener al menos un estado")
    if initial_state is not None and initial_state not in state_set:
        errors.append(f"initial_state: '{initial_state}' no está en states")
    for q in accept_states:
        if q not in state_set:
            errors.append(f"accept_states: '{q}' no está en states")

    for a in input_alphabet:
        if len(a) != 1:
            errors.append(f"input_alphabet: '{a}' debe ser un único carácter para poder leer las cadenas")
        if a not in tape_set:
            errors.append(f"input_alphabet: '{a}' no está en tape_alphabet")
    if BLANK not in tape_set:
        errors.append(f"tape_alphabet: debe incluir el símbolo blanco '{BLANK}'")
    if BLANK in input_alphabet:
        errors.append(f"input_alphabet: no puede incluir el símbolo blanco '{BLANK}'")

    transitions = _parse_transitions(mt["transitions"], state_set, tape_set, errors)
    inputs = _parse_inputs(mt["inputs"], errors)

    if errors:
        raise ConfigError(errors)

    return TuringMachine(
        states=states,
        input_alphabet=input_alphabet,
        tape_alphabet=tape_alphabet,
        initial_state=initial_state,
        accept_states=set(accept_states),
        transitions=transitions,
        inputs=inputs,
    )


def _parse_transitions(raw, state_set, tape_set, errors):
    if raw is None:
        return {}
    if not isinstance(raw, list):
        errors.append("transitions: debe ser una lista")
        return {}

    table = {}
    for i, item in enumerate(raw):
        where = f"transitions[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: debe ser un mapa con {list(TRANSITION_FIELDS)}")
            continue
        missing = [f for f in TRANSITION_FIELDS if f not in item]
        if missing:
            errors.append(f"{where}: faltan los campos {missing}")
            continue

        local = []
        state = _symbol(item["state"], f"{where}.state", local)
        next_state = _symbol(item["next"], f"{where}.next", local)
        move = _symbol(item["move"], f"{where}.move", local)
        read = _symbol_pair(item["read"], f"{where}.read", local)
        write = _symbol_pair(item["write"], f"{where}.write", local)

        for name, q in (("state", state), ("next", next_state)):
            if q is not None and q not in state_set:
                local.append(f"{where}.{name}: '{q}' no está en states")
        for name, pair in (("read", read), ("write", write)):
            for sym in pair or ():
                if sym not in tape_set:
                    local.append(f"{where}.{name}: '{sym}' no está en tape_alphabet")
        if move is not None and move not in MOVES:
            local.append(f"{where}.move: '{move}' no es válido (use {', '.join(MOVES)})")

        if local:
            errors.extend(local)
            continue

        # read: [símbolo en cinta, caché actual]   write: [nueva caché, símbolo a escribir]
        t = Transition(
            state=state,
            read_symbol=read[0],
            read_cache=read[1],
            next_state=next_state,
            write_cache=write[0],
            write_symbol=write[1],
            move=move,
        )
        if t.key in table:
            errors.append(
                f"{where}: transición duplicada para ([{state}, {read[1]}], {read[0]}); "
                "la máquina debe ser determinista"
            )
            continue
        table[t.key] = t
    return table


def _symbol_pair(value, where, errors):
    if not isinstance(value, list) or len(value) != 2:
        errors.append(f"{where}: debe ser una lista de dos símbolos [x, y]")
        return None
    pair = [_symbol(v, f"{where}[{i}]", errors) for i, v in enumerate(value)]
    return None if None in pair else pair


def _parse_inputs(raw, errors):
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append("inputs: debe ser una lista de cadenas")
        return []
    inputs = []
    for i, item in enumerate(raw):
        if item is None:
            inputs.append("")  # cadena vacía
        elif isinstance(item, str):
            inputs.append(item)
        else:
            # p.ej. 0101 sin comillas se lee como número y pierde su forma original
            errors.append(f"inputs[{i}]: '{item}' no es una cadena; escríbala entre comillas")
    return inputs
