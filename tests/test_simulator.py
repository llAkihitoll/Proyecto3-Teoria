import pytest

from turing import Outcome, parse_machine, simulate, simulate_all


def machine(transitions, accept=("qf",), states=("q0", "q1", "qf"), inputs=()):
    return parse_machine({
        "mt": {
            "states": list(states),
            "input_alphabet": ["a", "b"],
            "tape_alphabet": ["a", "b", "B", "X"],
            "initial_state": "q0",
            "accept_states": list(accept),
            "transitions": [
                {"state": s, "read": r, "write": w, "move": m, "next": n}
                for s, r, w, m, n in transitions
            ],
            "inputs": list(inputs),
        }
    })


# Acepta a+ : recorre las a hacia la derecha y acepta al encontrar blank.
A_PLUS = machine([
    ("q0", ["a", "B"], ["B", "a"], "R", "q1"),
    ("q1", ["a", "B"], ["B", "a"], "R", "q1"),
    ("q1", ["B", "B"], ["B", "B"], "L", "qf"),
])

# Usa la caché: guarda el primer símbolo, lo marca con X y lo copia al final.
COPY_FIRST = machine([
    ("q0", ["a", "B"], ["a", "X"], "R", "q1"),
    ("q0", ["b", "B"], ["b", "X"], "R", "q1"),
    ("q1", ["a", "a"], ["a", "a"], "R", "q1"),
    ("q1", ["b", "a"], ["a", "b"], "R", "q1"),
    ("q1", ["a", "b"], ["b", "a"], "R", "q1"),
    ("q1", ["b", "b"], ["b", "b"], "R", "q1"),
    ("q1", ["B", "a"], ["B", "a"], "S", "qf"),
    ("q1", ["B", "b"], ["B", "b"], "S", "qf"),
])

LOOP = machine([("q0", ["B", "B"], ["B", "B"], "S", "q0")])


def test_accepts_when_reaching_accept_state():
    result = simulate(A_PLUS, "aaa")
    assert result.outcome is Outcome.ACCEPTED
    assert result.steps == 4
    assert result.ids[-1].state == "qf"
    assert result.final_tape == "aaa"


def test_rejects_when_no_transition_applies():
    result = simulate(A_PLUS, "aab")
    assert result.outcome is Outcome.REJECTED
    assert result.ids[-1].state == "q1"
    assert "δ([q1, B], b)" in result.message


def test_rejects_when_initial_transition_missing():
    result = simulate(A_PLUS, "")
    assert result.outcome is Outcome.REJECTED
    assert result.steps == 0
    assert len(result.ids) == 1


def test_ids_record_every_step():
    result = simulate(A_PLUS, "aa")
    assert [str(i) for i in result.ids] == [
        "[q0, B] a a",
        "a [q1, B] a",
        "a a [q1, B] B",
        "a [qf, B] a",
    ]
    assert [i.step for i in result.ids] == [0, 1, 2, 3]


def test_cache_is_stored_and_used():
    result = simulate(COPY_FIRST, "bab")
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == "Xabb"
    # la última transición vacía la caché (write: [B, b]) al copiar el símbolo
    assert [i.cache for i in result.ids] == ["B", "b", "b", "b", "B"]
    assert str(result.ids[-1]) == "X a b [qf, B] b"


def test_accepts_immediately_if_initial_state_is_accepting():
    m = machine([("q0", ["a", "B"], ["B", "a"], "R", "q0")], accept=["q0"])
    result = simulate(m, "aaa")
    assert result.outcome is Outcome.ACCEPTED
    assert result.steps == 0


def test_invalid_input_is_not_simulated():
    result = simulate(A_PLUS, "abc")
    assert result.outcome is Outcome.INVALID_INPUT
    assert result.ids == []
    assert "c" in result.message


def test_infinite_loop_stops_at_step_limit():
    result = simulate(LOOP, "", max_steps=50)
    assert result.outcome is Outcome.STEP_LIMIT
    assert result.steps == 50
    assert len(result.ids) == 51


def test_halting_exactly_at_limit_is_not_reported_as_limit():
    # "aa" necesita exactamente 3 pasos para aceptar
    assert simulate(A_PLUS, "aa", max_steps=3).outcome is Outcome.ACCEPTED
    assert simulate(A_PLUS, "aa", max_steps=2).outcome is Outcome.STEP_LIMIT
    # "ab" se rechaza tras 1 paso
    assert simulate(A_PLUS, "ab", max_steps=1).outcome is Outcome.REJECTED


def test_negative_step_limit_is_an_error():
    with pytest.raises(ValueError):
        simulate(A_PLUS, "a", max_steps=-1)


def test_simulate_all_runs_every_configured_input():
    m = machine(
        [
            ("q0", ["a", "B"], ["B", "a"], "R", "q1"),
            ("q1", ["B", "B"], ["B", "B"], "L", "qf"),
        ],
        inputs=["a", "b", "aa"],
    )
    results = simulate_all(m)
    assert [r.input_word for r in results] == ["a", "b", "aa"]
    assert [r.outcome for r in results] == [Outcome.ACCEPTED, Outcome.REJECTED, Outcome.REJECTED]


def test_move_left_past_input_start():
    m = machine([
        ("q0", ["a", "B"], ["B", "a"], "L", "q1"),
        ("q1", ["B", "B"], ["B", "X"], "S", "qf"),
    ])
    result = simulate(m, "a")
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == "Xa"
    assert str(result.ids[1]) == "[q1, B] B a"
