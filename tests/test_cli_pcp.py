from pathlib import Path

import pytest

from main import main
from turing import load_machine, simulate_all
from turing.formatter import format_pcp_entry, format_pcp_report

MACHINES = Path(__file__).resolve().parent.parent / "machines"

TINY_YAML = """
mt:
  states: [q0, qf]
  input_alphabet: [a]
  tape_alphabet: [a, B]
  initial_state: q0
  accept_states: [qf]
  transitions:
    - state: q0
      read: [a, B]
      write: [B, a]
      move: R
      next: q0
    - state: q0
      read: [B, B]
      write: [B, B]
      move: S
      next: qf
  inputs:
    - "a"
    - "z"
"""


@pytest.fixture
def tiny(tmp_path):
    path = tmp_path / "tiny.yaml"
    path.write_text(TINY_YAML, encoding="utf-8")
    return path


def test_pcp_is_not_shown_by_default(tiny, capsys):
    assert main([str(tiny)]) == 0
    assert "REDUCCIÓN MT → PCP" not in capsys.readouterr().out


def test_pcp_option_lists_dominoes_and_solution(tiny, capsys):
    assert main([str(tiny), "--pcp"]) == 0
    out = capsys.readouterr().out
    assert "REDUCCIÓN MT → PCP" in out
    assert "Variante: MPCP (toda solución debe comenzar con c1)" in out
    assert "c1  = (#, # [q0,B] a #)" in out
    assert "Secuencia solución" in out
    assert "¿Superior = inferior? SÍ" in out


def test_pcp_option_reports_invalid_input_without_crashing(tiny, capsys):
    assert main([str(tiny), "--pcp"]) == 0
    assert "Sin instancia PCP: Símbolos fuera del alfabeto de entrada: z" in capsys.readouterr().out


def test_pcp_with_rejected_word_says_there_is_no_solution(capsys):
    assert main([str(MACHINES / "reconocedora.yaml"), "--pcp", "--quiet"]) == 0
    out = capsys.readouterr().out
    assert out.count("¿Superior = inferior? SÍ") == 2
    assert out.count("Sin secuencia solución: la MT no acepta la cadena (RECHAZADA)") == 2


def test_pcp_quiet_hides_domino_table_and_concatenations(capsys):
    assert main([str(MACHINES / "reconocedora.yaml"), "--pcp", "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "Dominós (" not in out
    assert "Superior (concatenación)" not in out
    assert "Secuencia solución (" in out


def test_pcp_output_is_saved_to_the_output_file(tiny, tmp_path, capsys):
    out_file = tmp_path / "salida.txt"
    assert main([str(tiny), "--pcp", "--output", str(out_file)]) == 0
    printed = capsys.readouterr().out
    assert out_file.read_text(encoding="utf-8").strip() == printed.strip()
    assert "REDUCCIÓN MT → PCP" in printed


def test_pcp_after_step_mode(tiny, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert main([str(tiny), "--step", "--pcp"]) == 0
    out = capsys.readouterr().out
    assert out.index("RESUMEN") < out.index("REDUCCIÓN MT → PCP")


def test_entry_with_reserved_separator_reports_the_error(tmp_path):
    machine = load_machine(MACHINES / "reconocedora.yaml")
    machine.tape_alphabet = list(machine.tape_alphabet) + ["#"]
    result = simulate_all(machine)[0]
    text = format_pcp_entry(machine, result)
    assert "No se pudo construir la instancia PCP" in text
    assert "reservado" in text


def test_report_has_one_entry_per_word():
    machine = load_machine(MACHINES / "reconocedora.yaml")
    results = simulate_all(machine)
    text = format_pcp_report(machine, results, quiet=True)
    assert text.count("PCP ") >= len(results)
    for i in range(1, len(results) + 1):
        assert f"PCP {i}/{len(results)}:" in text
