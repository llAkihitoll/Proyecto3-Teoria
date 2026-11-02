import copy
from pathlib import Path

import pytest

from turing import ConfigError, load_machine, parse_machine

MACHINES = Path(__file__).resolve().parent.parent / "machines"

BASE = {
    "mt": {
        "states": ["q0", "q1", "qf"],
        "input_alphabet": ["a", "b"],
        "tape_alphabet": ["a", "b", "B", "X"],
        "initial_state": "q0",
        "accept_states": ["qf"],
        "transitions": [
            {"state": "q0", "read": ["a", "B"], "write": ["a", "X"], "move": "R", "next": "q1"},
            {"state": "q1", "read": ["B", "a"], "write": ["B", "a"], "move": "L", "next": "qf"},
        ],
        "inputs": ["ab", "aab"],
    }
}


def config(**overrides):
    data = copy.deepcopy(BASE)
    data["mt"].update(overrides)
    return data


def errors_of(data):
    with pytest.raises(ConfigError) as exc:
        parse_machine(data)
    return "\n".join(exc.value.errors)


# --- configuraciones válidas ---

def test_load_pdf_example():
    m = load_machine(MACHINES / "ejemplo_pdf.yaml")
    assert m.states == ["q0", "q1", "q2", "qf"]
    assert m.input_alphabet == ["a", "b"]
    assert m.tape_alphabet == ["a", "b", "B", "X", "Y"]
    assert m.initial_state == "q0"
    assert m.accept_states == {"qf"}
    assert m.inputs == ["aabb", "ab", "aaabbb"]
    assert len(m.transitions) == 2


def test_pdf_transitions_match_delta_notation():
    m = load_machine(MACHINES / "ejemplo_pdf.yaml")
    t1 = m.get_transition("q0", "B", "a")
    t2 = m.get_transition("q0", "B", "b")
    assert str(t1) == "δ([q0, B], a) = ([q1, a], B, R)"
    assert str(t2) == "δ([q0, B], b) = ([q1, b], B, R)"


def test_transition_fields_are_interpreted():
    m = parse_machine(BASE)
    t = m.get_transition("q0", "B", "a")
    assert (t.state, t.read_symbol, t.read_cache) == ("q0", "a", "B")
    assert (t.next_state, t.write_cache, t.write_symbol, t.move) == ("q1", "a", "X", "R")
    assert m.get_transition("q0", "B", "b") is None


def test_move_stay_is_accepted():
    data = config()
    data["mt"]["transitions"][0]["move"] = "S"
    assert parse_machine(data).get_transition("q0", "B", "a").move == "S"


def test_empty_transitions_and_empty_input():
    m = parse_machine(config(transitions=[], inputs=["", None]))
    assert m.transitions == {}
    assert m.inputs == ["", ""]


def test_numeric_symbols_are_converted_to_strings():
    data = config(input_alphabet=[0, 1], tape_alphabet=[0, 1, "B"], transitions=[], inputs=["0110"])
    m = parse_machine(data)
    assert m.input_alphabet == ["0", "1"]
    assert m.invalid_symbols("0120") == ["2"]


# --- configuraciones inválidas ---

def test_missing_root():
    assert "'mt'" in errors_of({"states": []})


def test_missing_required_fields():
    data = copy.deepcopy(BASE)
    del data["mt"]["initial_state"]
    del data["mt"]["inputs"]
    msg = errors_of(data)
    assert "mt.initial_state" in msg and "mt.inputs" in msg


def test_initial_and_accept_states_must_exist():
    msg = errors_of(config(initial_state="qx", accept_states=["qz"]))
    assert "initial_state: 'qx'" in msg
    assert "accept_states: 'qz'" in msg


def test_input_alphabet_must_be_subset_of_tape_alphabet():
    assert "'c' no está en tape_alphabet" in errors_of(config(input_alphabet=["a", "c"]))


def test_blank_required_in_tape_and_forbidden_in_input():
    assert "símbolo blanco" in errors_of(config(tape_alphabet=["a", "b", "X"]))
    assert "no puede incluir el símbolo blanco" in errors_of(config(input_alphabet=["a", "B"]))


def test_input_symbols_must_be_single_characters():
    assert "único carácter" in errors_of(config(input_alphabet=["ab"], tape_alphabet=["ab", "B"]))


def test_duplicate_elements():
    assert "repetidos" in errors_of(config(states=["q0", "q0", "q1", "qf"]))


def test_transition_with_unknown_state_and_symbol():
    data = config()
    data["mt"]["transitions"][0].update(next="q9", read=["z", "B"])
    msg = errors_of(data)
    assert "next: 'q9'" in msg
    assert "read: 'z'" in msg


def test_transition_invalid_move():
    data = config()
    data["mt"]["transitions"][0]["move"] = "D"
    assert "move: 'D'" in errors_of(data)


def test_transition_read_write_must_be_pairs():
    data = config()
    data["mt"]["transitions"][0]["read"] = "a"
    data["mt"]["transitions"][1]["write"] = ["a"]
    msg = errors_of(data)
    assert "transitions[0].read" in msg and "transitions[1].write" in msg


def test_transition_missing_fields():
    data = config()
    del data["mt"]["transitions"][0]["next"]
    assert "faltan los campos ['next']" in errors_of(data)


def test_nondeterministic_transitions_are_rejected():
    data = config()
    dup = dict(data["mt"]["transitions"][0], next="qf")
    data["mt"]["transitions"].append(dup)
    assert "determinista" in errors_of(data)


def test_boolean_symbol_requires_quotes():
    assert "booleano" in errors_of(config(states=["q0", "q1", "qf", True]))


def test_non_string_input_requires_quotes():
    assert "entre comillas" in errors_of(config(inputs=[101]))


def test_all_errors_are_reported_together():
    data = config(initial_state="qx", accept_states=["qz"])
    with pytest.raises(ConfigError) as exc:
        parse_machine(data)
    assert len(exc.value.errors) == 2


def test_file_not_found_and_invalid_yaml(tmp_path):
    with pytest.raises(ConfigError, match="No se encontró"):
        load_machine(tmp_path / "no_existe.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("mt: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="no es un YAML válido"):
        load_machine(bad)
