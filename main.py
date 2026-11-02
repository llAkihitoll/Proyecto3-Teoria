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
    args = parser.parse_args(argv)
    if args.max_steps < 0:
        parser.error("--max-steps no puede ser negativo")

    try:
        machine = load_machine(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    results = simulate_all(machine, args.max_steps)
    print(format_report(machine, results, args.config))
    return 0


if __name__ == "__main__":
    sys.exit(main())
