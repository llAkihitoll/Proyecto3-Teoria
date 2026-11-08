"""Pruebas de la MT de codificación de Gödel (machines/godel.yaml).

Fase 1 — validación: la MT acepta exactamente las expresiones de la gramática
    N := 0 | S(N);  Suma := N (+ N)*;  Expr := Suma | Suma = Suma
y deja en la cinta  expresión # 1  con el cabezal al inicio.
"""

from itertools import product
from pathlib import Path

import pytest

from turing import Outcome, load_machine, simulate

MACHINES = Path(__file__).resolve().parent.parent / "machines"


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
def test_valid_expressions_pass_validation(godel, word):
    result = simulate(godel, word)
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == word + "#1"
    last = result.ids[-1]
    assert last.head == 0


@pytest.mark.parametrize("word", INVALID)
def test_invalid_expressions_are_rejected_by_the_machine(godel, word):
    result = simulate(godel, word)
    assert result.outcome is Outcome.REJECTED


def test_validation_matches_grammar_for_all_short_words(godel):
    for alphabet, max_len in (("0S()+=", 6), ("0S()+=*-/^", 5)):
        for n in range(max_len + 1):
            for symbols in product(alphabet, repeat=n):
                word = "".join(symbols)
                result = simulate(godel, word)
                expected = Outcome.ACCEPTED if is_expression(word) else Outcome.REJECTED
                assert result.outcome is expected, word


def test_validation_handles_long_expressions(godel):
    word = "S(S(S(S(S(0)))))+S(S(S(0)))=S(S(S(S(S(S(S(S(0))))))))"
    result = simulate(godel, word, max_steps=100_000)
    assert result.outcome is Outcome.ACCEPTED
    assert result.final_tape == word + "#1"
