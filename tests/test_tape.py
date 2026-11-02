from turing import Tape


def test_initial_tape_places_head_on_first_symbol():
    tape = Tape("abb")
    assert tape.read() == "a"
    assert tape.snapshot() == (("a", "b", "b"), 0)
    assert tape.content() == "abb"


def test_empty_input_shows_blank_under_head():
    tape = Tape("")
    assert tape.read() == "B"
    assert tape.snapshot() == (("B",), 0)
    assert tape.content() == ""


def test_write_replaces_symbol():
    tape = Tape("ab")
    tape.write("X")
    assert tape.read() == "X"
    assert tape.content() == "Xb"


def test_move_right_beyond_input_reads_blank():
    tape = Tape("a")
    tape.move("R")
    assert tape.read() == "B"
    assert tape.snapshot() == (("a", "B"), 1)


def test_move_left_beyond_start_extends_tape():
    tape = Tape("ab")
    tape.move("L")
    assert tape.head == -1
    assert tape.read() == "B"
    tape.write("Y")
    assert tape.snapshot() == (("Y", "a", "b"), 0)
    assert tape.content() == "Yab"


def test_stay_does_not_move_head():
    tape = Tape("ab")
    tape.move("S")
    assert tape.head == 0


def test_writing_blank_keeps_inner_blanks_and_trims_edges():
    tape = Tape("abc")
    tape.move("R")
    tape.write("B")
    assert tape.content() == "aBc"
    tape.move("L")
    tape.write("B")
    assert tape.content() == "c"
    assert tape.snapshot() == (("B", "B", "c"), 0)


def test_tape_with_only_blanks_has_empty_content():
    tape = Tape("a")
    tape.write("B")
    assert tape.content() == ""
