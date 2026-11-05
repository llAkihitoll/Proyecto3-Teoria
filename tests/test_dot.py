from turing import parse_machine
from turing.dot import to_dot

MACHINE = parse_machine({
    "mt": {
        "states": ["q0", "q1", "qf"],
        "input_alphabet": ["a"],
        "tape_alphabet": ["a", "B", "X"],
        "initial_state": "q0",
        "accept_states": ["qf"],
        "transitions": [
            {"state": "q0", "read": ["a", "B"], "write": ["B", "X"], "move": "R", "next": "q0"},
            {"state": "q0", "read": ["B", "B"], "write": ["B", "B"], "move": "L", "next": "qf"},
        ],
        "inputs": [],
    }
})


def test_dot_output_is_a_valid_digraph():
    text = to_dot(MACHINE)
    assert text.startswith("digraph MT {")
    assert text.endswith("}")


def test_dot_marks_the_initial_state():
    text = to_dot(MACHINE)
    assert '__inicio -> "q0"' in text


def test_dot_uses_doublecircle_only_for_accept_states():
    text = to_dot(MACHINE)
    assert '"qf" [shape=doublecircle];' in text
    assert '"q0" [shape=circle];' in text
    assert '"q1" [shape=circle];' in text


def test_dot_has_one_edge_per_transition_with_a_label():
    text = to_dot(MACHINE)
    assert '"q0" -> "q0" [label="a,B / X,B ; R"];' in text
    assert '"q0" -> "qf" [label="B,B / B,B ; L"];' in text


def test_dot_escapes_quotes_in_state_names():
    m = parse_machine({
        "mt": {
            "states": ['q"0', "qf"],
            "input_alphabet": ["a"],
            "tape_alphabet": ["a", "B"],
            "initial_state": 'q"0',
            "accept_states": ["qf"],
            "transitions": [],
            "inputs": [],
        }
    })
    text = to_dot(m)
    assert '"q\\"0"' in text
