import pytest

from turing import Domino, build_pcp, parse_machine

P0 = "[q0,B]"
PF = "[qf,B]"


def machine(transitions, states=("q0", "qf"), accept=("qf",), tape=("a", "B")):
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


# Recorre las a hacia la derecha y, al llegar al blanco, acepta sin mover el cabezal.
RIGHT_THEN_STAY = machine([
    ("q0", ["a", "B"], ["B", "a"], "R", "q0"),
    ("q0", ["B", "B"], ["B", "B"], "S", "qf"),
])

GOES_LEFT = machine(
    [
        ("q0", ["a", "B"], ["B", "a"], "R", "q1"),
        ("q1", ["B", "B"], ["B", "B"], "L", "q2"),
    ],
    states=("q0", "q1", "q2"),
    accept=("q2",),
)


def dom(top, bottom):
    return Domino(top.split(), bottom.split())


def index_of(instance, top, bottom):
    return instance.dominoes.index(dom(top, bottom)) + 1


def test_first_domino_is_the_initial_one():
    instance = build_pcp(RIGHT_THEN_STAY, "aa")
    assert instance.get(1) == dom("#", f"# {P0} a a #")
    assert instance.start_index == 1


def test_empty_word_leaves_the_head_on_the_right_edge():
    instance = build_pcp(RIGHT_THEN_STAY, "")
    assert instance.get(1) == dom("#", f"# {P0} #")


def test_copy_dominoes_cover_tape_alphabet_and_separator():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    assert [instance.get(i) for i in (2, 3, 4)] == [dom("a", "a"), dom("B", "B"), dom("#", "#")]


def test_right_move_domino():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    assert dom(f"{P0} a", f"a {P0}") in instance.dominoes


def test_blank_read_has_an_inner_and_an_edge_domino():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    assert dom(f"{P0} B", f"{PF} B") in instance.dominoes
    assert dom(f"{P0} #", f"{PF} B #") in instance.dominoes


def test_left_move_has_one_domino_per_tape_symbol():
    instance = build_pcp(GOES_LEFT, "a")
    p1, p2 = "[q1,B]", "[q2,B]"
    for c in ("a", "B"):
        assert dom(f"{c} {p1} B", f"{p2} {c} B") in instance.dominoes
        assert dom(f"{c} {p1} #", f"{p2} {c} B #") in instance.dominoes


def test_accepting_state_gets_erasing_and_closing_dominoes():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    for x in ("a", "B"):
        assert dom(f"{x} {PF}", PF) in instance.dominoes
        assert dom(f"{PF} {x}", PF) in instance.dominoes
    assert dom(f"{PF} # #", "#") in instance.dominoes


def test_domino_count_of_a_small_machine():
    # 1 inicial + 3 copia + 3 transición + 4 borrado + 1 cierre
    assert len(build_pcp(RIGHT_THEN_STAY, "a")) == 12


def test_no_dominoes_are_built_from_accepting_states():
    with_exit = machine([
        ("q0", ["B", "B"], ["B", "B"], "S", "qf"),
        ("qf", ["B", "B"], ["B", "B"], "R", "qf"),
    ])
    assert dom(f"{PF} B", f"B {PF}") not in build_pcp(with_exit, "").dominoes


def test_computation_history_is_a_solution():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    steps = [
        ("#", f"# {P0} a #"),
        (f"{P0} a", f"a {P0}"),
        ("#", "#"),
        ("a", "a"),
        (f"{P0} #", f"{PF} B #"),
        (f"a {PF}", PF),
        ("B", "B"),
        ("#", "#"),
        (f"{PF} B", PF),
        ("#", "#"),
        (f"{PF} # #", "#"),
    ]
    indices = [index_of(instance, top, bottom) for top, bottom in steps]
    check = instance.check(indices)
    assert check.top == check.bottom
    assert instance.is_solution(indices)


def test_solution_must_start_with_the_initial_domino():
    instance = build_pcp(RIGHT_THEN_STAY, "a")
    copy_a = index_of(instance, "a", "a")
    assert instance.check([copy_a]).top == instance.check([copy_a]).bottom
    assert not instance.is_solution([copy_a])


def test_word_outside_the_input_alphabet_is_rejected():
    with pytest.raises(ValueError, match="alfabeto"):
        build_pcp(RIGHT_THEN_STAY, "ab")


def test_separator_cannot_be_a_tape_symbol():
    reserved = machine([("q0", ["a", "B"], ["B", "a"], "R", "q0")], tape=("a", "B", "#"))
    with pytest.raises(ValueError, match="reservado"):
        build_pcp(reserved, "a")
