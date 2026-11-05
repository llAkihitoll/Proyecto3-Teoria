import pytest

from turing.pcp import Domino, PCPInstance


def dom(top, bottom):
    return Domino(top.split(), bottom.split())


def classic_instance():
    return PCPInstance([dom("b", "c a"), dom("a b", "a"), dom("c a", "a b"), dom("a", "b c")])


def test_domino_str_uses_epsilon_for_empty_side():
    assert str(Domino(["0", "0", "qA", "1", "#"], [])) == "(0 0 qA 1 #, ε)"


def test_domino_tokens_can_be_multi_character():
    domino = Domino(["[q0,B]", "a"], ["X", "q10"])
    assert domino.top == ("[q0,B]", "a")
    assert domino.bottom == ("X", "q10")


def test_known_solution_is_accepted():
    instance = PCPInstance([dom("a", "a b"), dom("b", "c a"), dom("c a", "a"), dom("a b c", "c")])
    check = instance.check([1, 2, 3, 1, 4])
    assert check.top == check.bottom
    assert instance.is_solution([1, 2, 3, 1, 4])


def test_non_matching_sequence_is_rejected():
    instance = classic_instance()
    check = instance.check([1, 2])
    assert check.top != check.bottom
    assert not check.is_solution


def test_empty_sequence_is_not_a_solution():
    assert not classic_instance().is_solution([])


def test_check_exposes_both_concatenations():
    instance = PCPInstance([dom("a", "a b"), dom("b a", "a")])
    check = instance.check([1, 2])
    assert check.top == ("a", "b", "a")
    assert check.bottom == ("a", "b", "a")


def test_epsilon_domino_contributes_nothing():
    instance = PCPInstance([dom("a", "a"), Domino(["x"], [])])
    check = instance.check([1, 2])
    assert check.top == ("a", "x")
    assert check.bottom == ("a",)


def test_indices_are_one_based():
    instance = classic_instance()
    assert instance.get(1) == dom("b", "c a")
    assert len(instance) == 4


@pytest.mark.parametrize("index", [0, 5, -1])
def test_out_of_range_index_raises(index):
    with pytest.raises(ValueError, match="fuera de rango"):
        classic_instance().check([index])
