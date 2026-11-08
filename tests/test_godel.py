"""Pruebas de la MT de codificación de Gödel (machines/godel.yaml).

Fase 1 — validación: la MT acepta exactamente las expresiones de la gramática
    N := 0 | S(N);  Op := + | - | * | / | ^;  Suma := N (Op N)*;  Expr := Suma | Suma = Suma
Fase 2 — codificación: cada símbolo se marca con X y su código de 4 bits se escribe después
    de  # 1;  la cinta final es  X...X # 1 bits  con el cabezal sobre el '#'.
"""

from itertools import product
from pathlib import Path

import pytest

from turing import Outcome, load_machine, simulate

MACHINES = Path(__file__).resolve().parent.parent / "machines"

CODES = {
    "0": "0001",
    "S": "0010",
    "(": "0011",
    ")": "0100",
    "+": "0101",
    "=": "0110",
    "*": "0111",
    "-": "1000",
    "/": "1001",
    "^": "1010",
}


def encode(word):
    return "1" + "".join(CODES[c] for c in word)


def phase2_tape(word):
    return "X" * len(word) + "#" + encode(word)


def _numeral(s, i):
    if s.startswith("0", i):
        return i + 1
    if s.startswith("S(", i):
        j = _numeral(s, i + 2)
        if j is not None and s.startswith(")", j):
            return j + 1
    return None


OPERATORS = "+-*/^"


def _suma(s, i):
    i = _numeral(s, i)
    while i is not None and i < len(s) and s[i] in OPERATORS:
        i = _numeral(s, i + 1)
    return i


def is_expression(s):
    i = _suma(s, 0)
    if i is not None and s.startswith("=", i):
        i = _suma(s, i + 1)
    return i == len(s)


@pytest.fixture(scope="module")
def godel():
    return load_machine(MACHINES / "godel.yaml")


VALID = [
    "0",
    "S(0)",
    "S(0)+S(0)",
    "S(S(0))=S(0)+S(0)",
    "0+0+0=0",
    "S(S(S(0)))",
    "S(0)+S(S(0))+0=S(S(S(0)))",
    "S(S(0))*S(0)-0/S(0)^0",
    "0^0=S(0)*S(0)",
]

INVALID = [
    "",
    "S",
    "S(",
    "S(0",
    "S0)",
    "S()",
    "(0)",
    "S(0))",
    "S(S(0)",
    "S(0+S(0))",
    "S(0)S(0)",
    "0+",
    "+0",
    "0++0",
    "0*/0",
    "0^",
    "-0",
    "/0",
    "S(0*S(0))",
    "S(0)^=0",
    "0=*0",
    "=0",
    "0=",
    "0=0=0",
    "0==0",
    "S(0)a",
    "a",
    "00",
    "0 + 0",
]


def test_reference_grammar_sanity():
    assert all(is_expression(w) for w in VALID)
    assert not any(is_expression(w) for w in INVALID)


@pytest.mark.parametrize("word", VALID)
def test_valid_expressions_are_accepted_and_encoded(godel, word):
    result = simulate(godel, word, max_steps=100_000)
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == phase2_tape(word)
    assert result.ids[-1].head == len(word)


def test_mandatory_example(godel):
    result = simulate(godel, "S(0)+S(0)")
    assert result.final_tape.split("#")[1] == "1001000110001010001010010001100010100"


def test_encoding_uses_four_bit_blocks_with_leading_one(godel):
    assert simulate(godel, "0").final_tape == "X#10001"
    assert len(simulate(godel, "S(0)+S(0)").final_tape.split("#")[1]) == 1 + 4 * 9


@pytest.mark.parametrize("word", INVALID)
def test_invalid_expressions_are_rejected_by_the_machine(godel, word):
    result = simulate(godel, word)
    assert result.outcome is Outcome.REJECTED


def test_machine_matches_grammar_and_encoding_for_all_short_words(godel):
    for alphabet, max_len in (("0S()+=", 6), ("0S()+=*-/^", 5)):
        for n in range(max_len + 1):
            for symbols in product(alphabet, repeat=n):
                word = "".join(symbols)
                result = simulate(godel, word, max_steps=100_000)
                if is_expression(word):
                    assert result.outcome is Outcome.ACCEPTED, word
                    assert result.final_tape == phase2_tape(word), word
                else:
                    assert result.outcome is Outcome.REJECTED, word


def test_long_expressions_with_variable_length(godel):
    word = "S(S(S(S(S(0)))))+S(S(S(0)))=S(S(S(S(S(S(S(S(0))))))))"
    result = simulate(godel, word, max_steps=100_000)
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == phase2_tape(word)
