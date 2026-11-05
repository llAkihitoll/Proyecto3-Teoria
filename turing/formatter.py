
from .models import Outcome

WIDTH = 70


def _rule(char="="):
    return char * WIDTH


def _quoted(word):
    return f'"{word}"' if word else '"" (cadena vacía)'


def format_machine(machine, source=""):
    title = "MÁQUINA DE TURING" + (f"  —  {source}" if source else "")
    accept = [q for q in machine.states if q in machine.accept_states]
    lines = [
        _rule(),
        title,
        _rule(),
        f"Estados (Q):               {', '.join(machine.states)}",
        f"Alfabeto de entrada (Σ):   {', '.join(machine.input_alphabet)}",
        f"Alfabeto de cinta (Γ):     {', '.join(machine.tape_alphabet)}",
        f"Símbolo blanco:            {machine.blank}",
        f"Estado inicial:            {machine.initial_state}",
        f"Estados de aceptación (F): {', '.join(accept)}",
        f"Transiciones ({len(machine.transitions)}):",
    ]
    lines += [f"  {t}" for t in machine.transitions.values()]
    return "\n".join(lines)


def format_tape(description):
    """Cinta de una ID con una marca bajo la celda del cabezal."""
    cells = " ".join(description.tape)
    offset = sum(len(s) + 1 for s in description.tape[: description.head])
    return cells, " " * offset + "^"


def format_warnings(warnings):
    """Bloque de advertencias sobre el YAML; cadena vacía si no hay ninguna."""
    if not warnings:
        return ""
    lines = ["", _rule("-"), "ADVERTENCIAS", _rule("-")]
    lines += [f"  - {w}" for w in warnings]
    return "\n".join(lines)


def format_result_header(result, index=1, total=1):
    """Título de la entrada y, si la cadena es inválida, también el resultado."""
    lines = [
        "",
        _rule("-"),
        f"Entrada {index}/{total}: {_quoted(result.input_word)}",
        _rule("-"),
    ]
    if result.outcome is Outcome.INVALID_INPUT:
        lines += [f"Resultado: {result.outcome.value}", f"Motivo:    {result.message}"]
    else:
        lines.append("Descripciones instantáneas:")
    return "\n".join(lines)


def format_id_line(desc, index, width):
    """Una línea de la ID `desc`; `index` es su posición dentro de la lista de IDs."""
    prefix = "  " if index == 0 else "⊢ "
    return f"  {prefix}{desc.step:>{width}}:  {desc}"


def format_result_footer(result):
    """Configuración final de la cinta y el resultado de la simulación."""
    final = result.ids[-1]
    cells, marker = format_tape(final)
    lines = [
        "",
        "Configuración final:",
        f"  ID:          {final}",
        f"  Estado:      [{final.state}, {final.cache}]",
        f"  Cinta:       {cells}",
        f"               {marker}",
        f"  Contenido:   {result.final_tape or '(solo blancos)'}",
        f"  Pasos:       {result.steps}",
        "",
        f"Resultado: {result.outcome.value}",
        f"Motivo:    {result.message}",
    ]
    return "\n".join(lines)


def format_result(result, index=1, total=1):
    if result.outcome is Outcome.INVALID_INPUT:
        return format_result_header(result, index, total)
    width = len(str(result.ids[-1].step))
    parts = [format_result_header(result, index, total)]
    parts += [format_id_line(desc, i, width) for i, desc in enumerate(result.ids)]
    parts.append(format_result_footer(result))
    return "\n".join(parts)


def format_summary(results):
    rows = [
        (
            str(i),
            result.input_word or "ε",
            result.outcome.value,
            str(result.steps) if result.ids else "-",
            (result.final_tape or "(solo blancos)") if result.ids else "-",
        )
        for i, result in enumerate(results, 1)
    ]
    header = ("#", "Entrada", "Resultado", "Pasos", "Cinta final")
    widths = [max(len(r[c]) for r in rows + [header]) for c in range(len(header))]

    def line(row):
        return "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip()

    lines = ["", _rule(), "RESUMEN", _rule(), line(header)]
    lines += [line(r) for r in rows]
    return "\n".join(lines)


def format_report(machine, results, source="", quiet=False, warnings=None):
    parts = [format_machine(machine, source)]
    warning_block = format_warnings(warnings or [])
    if warning_block:
        parts.append(warning_block)
    total = len(results)
    if not quiet:
        parts += [format_result(r, i, total) for i, r in enumerate(results, 1)]
    if results:
        parts.append(format_summary(results))
    else:
        parts.append("\nEl archivo no contiene cadenas en 'inputs'.")
    return "\n".join(parts)
