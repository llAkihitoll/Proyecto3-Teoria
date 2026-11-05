
def _escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def to_dot(machine, name="MT"):
    """Representación de la máquina como grafo DOT, lista para `dot -Tpng`."""
    lines = [f"digraph {name} {{", "  rankdir=LR;", '  node [shape=circle, fontname="Helvetica"];']

    lines.append('  __inicio [shape=point, label=""];')
    lines.append(f'  __inicio -> "{_escape(machine.initial_state)}";')

    for q in machine.states:
        shape = "doublecircle" if q in machine.accept_states else "circle"
        lines.append(f'  "{_escape(q)}" [shape={shape}];')

    for t in machine.transitions.values():
        label = f"{t.read_symbol},{t.read_cache} / {t.write_symbol},{t.write_cache} ; {t.move}"
        lines.append(
            f'  "{_escape(t.state)}" -> "{_escape(t.next_state)}" [label="{_escape(label)}"];'
        )

    lines.append("}")
    return "\n".join(lines)
