"""Pruebas del modo `modo: godel` (reglas sin caché y rechazo de símbolos por la propia MT)."""

import copy

import pytest

from turing import ConfigError, Outcome, parse_machine, simulate
from turing.formatter import format_machine, format_result
from turing.models import MODE_STANDARD

ALPHABET = ["0", "S", "(", ")", "+", "=", "*", "-", "/", "^"]

BASE = {
    "modo": "godel",
    "mt": {
        "states": ["q0", "q1", "qf"],
        "input_alphabet": ALPHABET,
        "tape_alphabet": ALPHABET + ["B"],
        "initial_state": "q0",
        "accept_states": ["qf"],
        "transitions": [
            {"state": "q0", "read": "0", "write": "0", "move": "R", "next": "q1"},
            {"state": "q1", "read": "B", "write": "B", "move": "L", "next": "qf"},
        ],
        "inputs": ["0"],
    },
}


def config(**changes):
    data = copy.deepcopy(BASE)
    data.update(changes)
    return data


def errors_of(data):
    with pytest.raises(ConfigError) as exc:
        parse_machine(data)
    return "\n".join(exc.value.errors)


def test_mode_defaults_to_standard():
    data = copy.deepcopy(BASE)
    del data["modo"]
    data["mt"]["transitions"] = []
    assert parse_machine(data).mode == MODE_STANDARD


def test_godel_transitions_have_no_cache():
    m = parse_machine(BASE)
    t = m.get_transition("q0", "B", "0")
    assert (t.read_cache, t.write_cache) == ("B", "B")
    assert t.simple() == "δ(q0, 0) = (q1, 0, R)"


def test_unknown_mode_is_rejected():
    assert "modo" in errors_of(config(modo="otro"))


def test_godel_rejects_cache_pairs():
    data = config()
    data["mt"]["transitions"][0]["read"] = ["0", "B"]
    assert "no hay caché" in errors_of(data)


def test_godel_requires_fixed_input_alphabet():
    data = config()
    data["mt"]["input_alphabet"] = ["0", "S"]
    assert "input_alphabet" in errors_of(data)


def test_godel_does_not_filter_unknown_symbols_before_running():
    result = simulate(parse_machine(BASE), "0a")
    assert result.outcome is Outcome.REJECTED
    assert "δ(q1, a)" in result.message


def test_godel_output_has_no_cache():
    m = parse_machine(BASE)
    result = simulate(m, "0")
    assert str(result.ids[0]) == "[q0] 0"
    assert "[q0, B]" not in format_result(result)
    assert "δ(q0, 0) = (q1, 0, R)" in format_machine(m)
