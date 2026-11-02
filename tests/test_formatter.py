from turing import InstantaneousDescription, Outcome, SimulationResult, parse_machine, simulate
from turing.formatter import format_machine, format_report, format_result, format_summary, format_tape

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
        "inputs": ["aa", "b"],
    }
})


def test_format_machine_lists_formal_description():
    text = format_machine(MACHINE, "maquina.yaml")
    assert "maquina.yaml" in text
    assert "Estados (Q):               q0, q1, qf" in text
    assert "Alfabeto de entrada (Σ):   a" in text
    assert "Estados de aceptación (F): qf" in text
    assert "Transiciones (2):" in text
    assert "δ([q0, B], a) = ([q0, B], X, R)" in text


def test_format_tape_marks_head_position():
    desc = InstantaneousDescription(3, "q1", "B", ("X", "XY", "a"), 2)
    cells, marker = format_tape(desc)
    assert cells == "X XY a"
    assert marker == "     ^"
    assert cells[len(marker) - 1] == "a"


def test_format_result_shows_all_ids_and_final_configuration():
    text = format_result(simulate(MACHINE, "aa"), 1, 2)
    assert 'Entrada 1/2: "aa"' in text
    assert "    0:  [q0, B] a a" in text
    assert "  ⊢ 1:  X [q0, B] a" in text
    assert "  ⊢ 3:  X [qf, B] X" in text
    assert "Contenido:   XX" in text
    assert "Pasos:       3" in text
    assert "Resultado: ACEPTADA" in text


def test_format_result_for_invalid_input_has_no_ids():
    text = format_result(simulate(MACHINE, "b"))
    assert "Resultado: ENTRADA INVÁLIDA" in text
    assert "Descripciones instantáneas" not in text


def test_format_result_with_blank_tape_and_empty_word():
    result = SimulationResult(
        "", Outcome.REJECTED, [InstantaneousDescription(0, "q0", "B", ("B",), 0)], "", "sin transición"
    )
    text = format_result(result)
    assert '"" (cadena vacía)' in text
    assert "Contenido:   (solo blancos)" in text


def test_format_summary_has_one_row_per_input():
    results = [simulate(MACHINE, "aa"), simulate(MACHINE, "b")]
    lines = format_summary(results).splitlines()
    assert lines[-2].split() == ["1", "aa", "ACEPTADA", "3", "XX"]
    assert lines[-1].split()[:3] == ["2", "b", "ENTRADA"]


def test_format_report_without_inputs():
    machine = parse_machine({"mt": {**_mt(), "inputs": []}})
    assert "no contiene cadenas" in format_report(machine, [])


def _mt():
    return {
        "states": ["q0"],
        "input_alphabet": ["a"],
        "tape_alphabet": ["a", "B"],
        "initial_state": "q0",
        "accept_states": [],
        "transitions": [],
    }
