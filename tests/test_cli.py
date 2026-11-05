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
