"""Pruebas de integración: archivos YAML de demostración ejecutados con el motor general."""

import re
from itertools import product
from pathlib import Path

import pytest

from turing import Outcome, load_machine, simulate, simulate_all

MACHINES = Path(__file__).resolve().parent.parent / "machines"


def words(alphabet, max_len):
    for n in range(max_len + 1):
        for letters in product(alphabet, repeat=n):
            yield "".join(letters)


def in_anbncn(word):
    match = re.fullmatch(r"(a+)(b+)(c+)", word)
    return bool(match) and len({len(g) for g in match.groups()}) == 1


@pytest.fixture(scope="module")
def recognizer():
    return load_machine(MACHINES / "reconocedora.yaml")


@pytest.fixture(scope="module")
def duplicator():
    return load_machine(MACHINES / "alteradora.yaml")


# --- MT reconocedora: a^n b^n c^n ---

def test_recognizer_demo_inputs_meet_pdf_requirements(recognizer):
    results = simulate_all(recognizer)
    accepted = [r for r in results if r.outcome is Outcome.ACCEPTED]
    rejected = [r for r in results if r.outcome is Outcome.REJECTED]
    assert len(accepted) == 2 and len(rejected) == 2
    assert all(len(r.input_word) >= 5 for r in results)


def test_recognizer_demo_results(recognizer):
    outcomes = {r.input_word: r.outcome for r in simulate_all(recognizer)}
    assert outcomes == {
        "aabbcc": Outcome.ACCEPTED,
        "aaabbbccc": Outcome.ACCEPTED,
        "aabbbcc": Outcome.REJECTED,
        "abcabc": Outcome.REJECTED,
    }


def test_recognizer_matches_language_for_all_short_words(recognizer):
    for word in words("abc", 7):
        result = simulate(recognizer, word)
        expected = Outcome.ACCEPTED if in_anbncn(word) else Outcome.REJECTED
        assert result.outcome is expected, word


def test_recognizer_long_word(recognizer):
    n = 15
    assert simulate(recognizer, "a" * n + "b" * n + "c" * n).outcome is Outcome.ACCEPTED
    assert simulate(recognizer, "a" * n + "b" * n + "c" * (n - 1)).outcome is Outcome.REJECTED


# --- MT alteradora: w -> ww ---

def test_duplicator_demo_inputs_meet_pdf_requirements(duplicator):
    results = simulate_all(duplicator)
    assert len(results) == 4
    assert all(len(r.input_word) >= 5 for r in results)
    for r in results:
        assert r.outcome is Outcome.ACCEPTED
        assert r.final_tape == r.input_word * 2


def test_duplicator_doubles_all_short_words(duplicator):
    for word in words("ab", 7):
        result = simulate(duplicator, word)
        assert result.outcome is Outcome.ACCEPTED, word
        assert result.final_tape == word * 2, word


def test_duplicator_leaves_head_at_start_and_never_blanks_tape(duplicator):
    result = simulate(duplicator, "abbab")
    final = result.ids[-1]
    assert final.head == 0
    assert "".join(final.tape) == "abbababbab"
    assert all(set(d.tape) != {"B"} for d in result.ids)


def test_demo_machines_do_not_hit_step_limit(recognizer, duplicator):
    for machine in (recognizer, duplicator):
        for r in simulate_all(machine):
            assert r.outcome is not Outcome.STEP_LIMIT
