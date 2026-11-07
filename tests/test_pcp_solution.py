from pathlib import Path

import pytest

from turing import build_pcp, load_machine, parse_machine, solution_indices

MACHINES = Path(__file__).resolve().parent.parent / "machines"


def machine(transitions, states, accept, tape=("a", "B")):
    return parse_machine({
        "mt": {
            "states": list(states),
            "input_alphabet": ["a"],
            "tape_alphabet": list(tape),
            "initial_state": "q0",
            "accept_states": list(accept),
            "transitions": [
                {"state": s, "read": r, "write": w, "move": m, "next": n}
                for s, r, w, m, n in transitions
            ],
            "inputs": [],
        }
    })


RIGHT_THEN_STAY = machine(
    [
        ("q0", ["a", "B"], ["B", "a"], "R", "q0"),
        ("q0", ["B", "B"], ["B", "B"], "S", "qf"),
    ],
    states=("q0", "qf"),
    accept=("qf",),
)

# Va a la derecha y regresa con L hasta salirse por la izquierda de la celda 0.
WALKS_OFF_THE_LEFT = machine(
    [
        ("q0", ["a", "B"], ["B", "a"], "R", "q0"),
        ("q0", ["B", "B"], ["B", "B"], "L", "q1"),
        ("q1", ["a", "B"], ["B", "a"], "L", "q1"),
        ("q1", ["B", "B"], ["B", "B"], "S", "qf"),
    ],
    states=("q0", "q1", "qf"),
    accept=("qf",),
)

# Acepta de inmediato en el estado inicial.
ACCEPTS_AT_ONCE = machine([], states=("q0",), accept=("q0",))

LOOPS = machine(
    [("q0", ["B", "B"], ["B", "B"], "R", "q0")],
    states=("q0", "qf"),
    accept=("qf",),
)


@pytest.fixture(scope="module")
def recognizer():
    return load_machine(MACHINES / "reconocedora.yaml")


@pytest.fixture(scope="module")
def duplicator():
    return load_machine(MACHINES / "alteradora.yaml")


def assert_solves(m, word):
    instance = build_pcp(m, word)
    indices = solution_indices(m, word, instance)
    assert indices is not None
    assert indices[0] == 1
    check = instance.check(indices)
    assert check.top == check.bottom
    assert instance.is_solution(indices)
    return instance, indices


@pytest.mark.parametrize("word", ["", "a", "aaa"])
def test_simple_machine_solution(word):
    assert_solves(RIGHT_THEN_STAY, word)


def test_solution_matches_the_hand_built_sequence():
    instance, indices = assert_solves(RIGHT_THEN_STAY, "a")
    top = " ".join(instance.check(indices).top)
    assert top == "# [q0,B] a # a [q0,B] # a [qf,B] B # [qf,B] B # [qf,B] # #"


@pytest.mark.parametrize("word", ["", "a", "aaa"])
def test_tape_grows_to_the_left(word):
    assert_solves(WALKS_OFF_THE_LEFT, word)


def test_initial_state_can_be_accepting():
    instance, indices = assert_solves(ACCEPTS_AT_ONCE, "aa")
    assert indices[0] == 1 and indices[-1] == len(instance)


def test_rejected_word_has_no_solution_sequence():
    assert solution_indices(RIGHT_THEN_STAY, "a", max_steps=0) is None


def test_looping_machine_has_no_solution_sequence():
    assert solution_indices(LOOPS, "", max_steps=50) is None


@pytest.mark.parametrize("word", ["aabbcc", "aaabbbccc"])
def test_recognizer_accepted_words_have_a_solution(recognizer, word):
    assert_solves(recognizer, word)


@pytest.mark.parametrize("word", ["aabbbcc", "abcabc"])
def test_recognizer_rejected_words_have_no_solution(recognizer, word):
    assert solution_indices(recognizer, word) is None


@pytest.mark.parametrize("word", ["", "a", "ab", "bab"])
def test_duplicator_solution_even_when_it_reads_left_of_the_input(duplicator, word):
    assert_solves(duplicator, word)
