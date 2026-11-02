"""Cinta infinita en ambos sentidos con un único cabezal."""

from .models import BLANK, MOVES


class Tape:
    def __init__(self, word="", blank=BLANK):
        self.blank = blank
        # Solo se guardan las celdas no blancas; el resto de la cinta es blank.
        self.cells = {i: ch for i, ch in enumerate(word)}
        self.head = 0

    def read(self):
        return self.cells.get(self.head, self.blank)

    def write(self, symbol):
        if symbol == self.blank:
            self.cells.pop(self.head, None)
        else:
            self.cells[self.head] = symbol

    def move(self, direction):
        self.head += MOVES[direction]

    def snapshot(self):
        """Porción visible de la cinta (símbolos no blancos más la celda del cabezal).

        Devuelve (símbolos, índice del cabezal dentro de esa tupla).
        """
        positions = list(self.cells) + [self.head]
        start, end = min(positions), max(positions)
        symbols = tuple(self.cells.get(i, self.blank) for i in range(start, end + 1))
        return symbols, self.head - start

    def content(self):
        """Contenido de la cinta sin los blancos de los extremos."""
        if not self.cells:
            return ""
        start, end = min(self.cells), max(self.cells)
        return "".join(self.cells.get(i, self.blank) for i in range(start, end + 1))
