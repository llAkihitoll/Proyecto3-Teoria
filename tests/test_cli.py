from pathlib import Path

import pytest

from main import main

MACHINES = Path(__file__).resolve().parent.parent / "machines"

LOOP_YAML = """
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
      move: S
      next: q0
  inputs:
    - "aaaaa"
"""


def test_runs_pdf_example(capsys):
    assert main([str(MACHINES / "ejemplo_pdf.yaml")]) == 0
    out = capsys.readouterr().out
    assert out.count("Resultado: RECHAZADA") == 3
    assert "RESUMEN" in out


def test_invalid_config_prints_error_and_returns_1(tmp_path, capsys):
    bad = tmp_path / "bad.yaml"
    bad.write_text("mt:\n  states: [q0]\n", encoding="utf-8")
    assert main([str(bad)]) == 1
    err = capsys.readouterr().err
    assert "Configuración inválida" in err
    assert "mt.transitions" in err


def test_missing_file_returns_1(capsys):
    assert main(["no_existe.yaml"]) == 1
    assert "No se encontró" in capsys.readouterr().err


def test_max_steps_option(tmp_path, capsys):
    loop = tmp_path / "loop.yaml"
    loop.write_text(LOOP_YAML, encoding="utf-8")
    assert main([str(loop), "--max-steps", "5"]) == 0
    out = capsys.readouterr().out
    assert "DETENIDA POR LÍMITE DE PASOS" in out
    assert "⊢ 5:" in out and "⊢ 6:" not in out


def test_negative_max_steps_is_rejected(capsys):
    with pytest.raises(SystemExit):
        main([str(MACHINES / "ejemplo_pdf.yaml"), "--max-steps", "-1"])


def test_quiet_mode_hides_ids_but_keeps_summary(capsys):
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "Descripciones instantáneas" not in out
    assert "RESUMEN" in out


def test_extra_input_is_simulated_without_touching_the_yaml_file(capsys):
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--input", "aaabbb"]) == 0
    out = capsys.readouterr().out
    assert 'Entrada 4/4: "aaabbb"' in out


def test_extra_input_can_be_repeated(capsys):
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--input", "a", "--input", "b"]) == 0
    out = capsys.readouterr().out
    assert 'Entrada 4/5: "a"' in out
    assert 'Entrada 5/5: "b"' in out


def test_output_option_saves_the_same_report_to_a_file(tmp_path, capsys):
    out_file = tmp_path / "salida.txt"
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--output", str(out_file)]) == 0
    printed = capsys.readouterr().out
    assert out_file.read_text(encoding="utf-8").strip() == printed.strip()


def test_step_mode_waits_for_enter_between_ids(monkeypatch, capsys):
    presses = []

    def fake_input(prompt=""):
        presses.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--step"]) == 0
    out = capsys.readouterr().out
    assert "Descripciones instantáneas" in out
    assert "RESUMEN" in out
    # cada entrada válida (q0 -> q1) genera 2 IDs: la inicial y la de después de leer
    assert len(presses) == 2 * 3


def test_step_mode_does_not_pause_for_invalid_input(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "invalida.yaml"
    config_path.write_text(
        """
mt:
  states: [q0, qf]
  input_alphabet: [a]
  tape_alphabet: [a, B]
  initial_state: q0
  accept_states: [qf]
  transitions: []
  inputs:
    - "z"
""",
        encoding="utf-8",
    )

    def fail_if_called(prompt=""):
        raise AssertionError("no debería pausar en una entrada inválida")

    monkeypatch.setattr("builtins.input", fail_if_called)
    assert main([str(config_path), "--step"]) == 0
    out = capsys.readouterr().out
    assert "ENTRADA INVÁLIDA" in out


def test_step_and_quiet_cannot_be_combined():
    with pytest.raises(SystemExit):
        main([str(MACHINES / "ejemplo_pdf.yaml"), "--step", "--quiet"])


def test_warnings_are_shown_for_the_pdf_example(capsys):
    assert main([str(MACHINES / "ejemplo_pdf.yaml")]) == 0
    out = capsys.readouterr().out
    assert "ADVERTENCIAS" in out
    assert "'q2' es inalcanzable" in out


def test_dot_option_writes_a_graphviz_file(tmp_path, capsys):
    dot_file = tmp_path / "diagrama.dot"
    assert main([str(MACHINES / "ejemplo_pdf.yaml"), "--dot", str(dot_file)]) == 0
    text = dot_file.read_text(encoding="utf-8")
    assert text.startswith("digraph MT {")
    out = capsys.readouterr().out
    assert f"Diagrama Graphviz guardado en '{dot_file}'" in out
    assert "RESUMEN" in out
