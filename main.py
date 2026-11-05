"""Simulador de Máquinas de Turing de una cinta.

Uso:
    python main.py machines/reconocedora.yaml
    python main.py machines/alteradora.yaml --max-steps 50000
"""

import argparse
import sys

from turing import DEFAULT_MAX_STEPS, ConfigError, load_machine, simulate_all
from turing.formatter import format_report


def main(argv=None):
    # Evita errores de codificación (δ, Σ, Γ, ⊢) al redirigir la salida en Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Simulador de Máquinas de Turing de una cinta")
    parser.add_argument("config", help="archivo YAML con la descripción de la máquina")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help=f"límite de pasos por cadena (por defecto {DEFAULT_MAX_STEPS})",
    )
    parser.add_argument(
        "--input",
        dest="extra_inputs",
        action="append",
        metavar="cadena",
        help="simula una cadena adicional sin modificar el YAML (se puede repetir)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="solo muestra la tabla resumen, sin las descripciones instantáneas de cada cadena",
    )
    parser.add_argument(
        "--output",
        metavar="archivo",
        help="además de mostrarla en pantalla, guarda la salida en este archivo",
    )
    args = parser.parse_args(argv)
    if args.max_steps < 0:
        parser.error("--max-steps no puede ser negativo")

    try:
        machine = load_machine(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.extra_inputs:
        machine.inputs = list(machine.inputs) + args.extra_inputs

    results = simulate_all(machine, args.max_steps)
    report = format_report(machine, results, args.config, quiet=args.quiet)
    print(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
