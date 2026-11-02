# Proyecto 3 — Simulador de Máquinas de Turing

Simulador de Máquinas de Turing (MT) **de una cinta** para el curso de Teoría de la Computación. El programa:

1. Lee la descripción formal de una MT desde un archivo YAML.
2. Simula cada cadena de entrada configurada en ese archivo.
3. Muestra todas las descripciones instantáneas (IDs) de la simulación.
4. Muestra la configuración final de la cinta.
5. Indica si cada cadena fue **aceptada** o **rechazada**.

## Requisitos

- Python 3.9 o superior (probado con Python 3.13 y 3.14)
- PyYAML (para leer los archivos de configuración)
- pytest (solo para ejecutar las pruebas)

## Instalación

```bash
git clone https://github.com/llAkihitoll/Proyecto3-Teoria.git
cd Proyecto3-Teoria
pip install -r requirements.txt
```

Opcionalmente, dentro de un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py <archivo.yaml> [--max-steps N]
```

| Argumento | Descripción |
|---|---|
| `archivo.yaml` | Descripción de la máquina y cadenas a simular |
| `--max-steps N` | Límite de pasos por cadena (por defecto 10 000) |

Máquinas incluidas:

```bash
python main.py machines/reconocedora.yaml   # MT reconocedora de a^n b^n c^n
python main.py machines/alteradora.yaml     # MT alteradora w -> ww
python main.py machines/ejemplo_pdf.yaml    # ejemplo literal del enunciado
```

Para guardar la salida en un archivo:

```bash
python main.py machines/alteradora.yaml > salida.txt
```

Si el YAML tiene errores, el programa los lista todos y termina con código de salida 1.

## Formato del archivo YAML

```yaml
mt:
  states: [q0, q1, q2, qf]
  input_alphabet: [a, b]
  tape_alphabet: [a, b, B, X, Y]
  initial_state: q0
  accept_states: [qf]
  transitions:
    - state: q0
      read: [a, B]
      write: [a, B]
      move: R
      next: q1
  inputs:
    - "aabb"
    - "ab"
```

| Campo | Significado |
|---|---|
| `states` | Conjunto de estados Q |
| `input_alphabet` | Alfabeto de entrada Σ (símbolos de un carácter) |
| `tape_alphabet` | Alfabeto de cinta Γ; contiene a Σ y al blanco `B` |
| `initial_state` | Estado inicial q0 |
| `accept_states` | Estados de aceptación F |
| `transitions` | Función de transición δ |
| `inputs` | Cadenas que se simularán |

### Interpretación de las transiciones

El enunciado traduce la transición del ejemplo así:

```
read: [a, B], write: [a, B], move: R, next: q1   ≡   δ([q0, B], a) = ([q1, a], B, R)
```

Es decir, se usa el modelo de MT con **almacenamiento en el estado** (caché): el estado efectivo es el par `[q, c]`, donde `c` es un símbolo de Γ guardado en el control finito. La caché empieza en `B`.

| Campo | Contenido |
|---|---|
| `state` | Estado actual q |
| `read: [x, c]` | `x` = símbolo leído en la cinta, `c` = valor actual de la caché |
| `write: [c', y]` | `c'` = nuevo valor de la caché, `y` = símbolo que se escribe en la cinta |
| `move` | `L` (izquierda), `R` (derecha) o `S` (no se mueve) |
| `next` | Estado siguiente |

Una máquina que no necesite caché simplemente lee y escribe `B` en la segunda/primera posición, respectivamente.

### Validaciones

El parser reporta **todos** los errores encontrados, por ejemplo:

- Falta la raíz `mt` o algún campo obligatorio.
- Estados o símbolos repetidos.
- `initial_state` o `accept_states` que no pertenecen a `states`.
- Σ no contenido en Γ, `B` ausente de Γ o presente en Σ.
- Transiciones con estados o símbolos desconocidos, `read`/`write` que no son pares, movimiento inválido o campos faltantes.
- Transiciones duplicadas para el mismo `(estado, caché, símbolo)` (la MT debe ser determinista).
- Valores que YAML convierte implícitamente (`yes`/`no` a booleano, `0101` a número); deben ir entre comillas.

Una cadena de `inputs` con símbolos fuera de Σ no detiene el programa: se reporta como **ENTRADA INVÁLIDA**.

## Salida

Para cada cadena se muestra:

```
----------------------------------------------------------------------
Entrada 4/4: "abcabc"
----------------------------------------------------------------------
Descripciones instantáneas:
    0:  [q0, B] a b c a b c
  ⊢ 1:  X [q1, B] b c a b c
  ⊢ 2:  X Y [q2, B] c a b c
  ⊢ 3:  X [q3, B] Y Z a b c
  ⊢ 4:  [q3, B] X Y Z a b c
  ⊢ 5:  X [q0, B] Y Z a b c
  ⊢ 6:  X Y [q4, B] Z a b c
  ⊢ 7:  X Y Z [q5, B] a b c

Configuración final:
  ID:          X Y Z [q5, B] a b c
  Estado:      [q5, B]
  Cinta:       X Y Z a b c
                     ^
  Contenido:   XYZabc
  Pasos:       7

Resultado: RECHAZADA
Motivo:    No existe δ([q5, B], a) y q5 no es un estado de aceptación
```

Cada ID sigue la notación `X1 … Xi-1 [q, c] Xi … Xn`: el par `[q, c]` aparece justo antes del símbolo que está bajo el cabezal. Se muestran los símbolos no blancos de la cinta y la celda del cabezal (los blancos de los extremos se omiten, como en la notación de Hopcroft). Al inicio se imprime la descripción formal de la máquina y al final una tabla resumen.

### Resultados posibles

| Resultado | Cuándo ocurre |
|---|---|
| ACEPTADA | La máquina entra en un estado de `accept_states` |
| RECHAZADA | No existe transición aplicable y el estado actual no es de aceptación |
| DETENIDA POR LÍMITE DE PASOS | Se alcanzó `--max-steps` sin que la máquina se detuviera (no se clasifica como aceptada ni rechazada) |
| ENTRADA INVÁLIDA | La cadena contiene símbolos fuera de Σ |

## Arquitectura

```
Proyecto3/
├── main.py                  # Interfaz de línea de comandos
├── turing/
│   ├── models.py            # Estructuras de datos
│   ├── parser.py            # Lectura y validación del YAML
│   ├── tape.py              # Cinta infinita y cabezal
│   ├── simulator.py         # Motor de simulación
│   └── formatter.py         # Presentación de resultados
├── machines/                # Máquinas en YAML
│   ├── reconocedora.yaml
│   ├── alteradora.yaml
│   └── ejemplo_pdf.yaml
└── tests/                   # Pruebas unitarias y de integración
```

Flujo de ejecución:

```
archivo.yaml ──► parser.load_machine ──► TuringMachine
                                              │
                         para cada cadena de inputs
                                              ▼
                      simulator.simulate ──► SimulationResult (lista de IDs)
                                              │
                                              ▼
                      formatter.format_report ──► texto en consola
```

Cada módulo tiene una sola responsabilidad: el parser no simula, el simulador no imprime y el formateador no calcula. Las máquinas de demostración no tienen ningún caso especial en el código: son solo archivos YAML que se ejecutan con el mismo motor.

### Estructuras de datos (`turing/models.py`)

| Estructura | Contenido |
|---|---|
| `Transition` | `state`, `read_symbol`, `read_cache`, `next_state`, `write_cache`, `write_symbol`, `move`. Se imprime como `δ([q, c], x) = ([p, c'], y, D)` |
| `TuringMachine` | Q, Σ, Γ, estado inicial, F, cadenas y la tabla δ como diccionario `(estado, caché, símbolo) → Transition`, de modo que cada búsqueda es O(1) |
| `InstantaneousDescription` | Número de paso, estado, caché, porción visible de la cinta y posición del cabezal en ella |
| `SimulationResult` | Cadena, resultado (`Outcome`), lista de IDs, contenido final de la cinta y motivo |
| `Outcome` | ACEPTADA, RECHAZADA, DETENIDA POR LÍMITE DE PASOS, ENTRADA INVÁLIDA |

### Cinta (`turing/tape.py`)

La cinta es infinita en ambos sentidos. Se representa con un diccionario `posición → símbolo` que guarda solo las celdas no blancas; cualquier otra posición contiene `B`. Así el cabezal puede moverse a posiciones negativas o más allá de la entrada sin redimensionar estructuras. La entrada se coloca desde la posición 0 y el cabezal inicia sobre el primer símbolo.

### Motor de simulación (`turing/simulator.py`)

```
si la cadena tiene símbolos fuera de Σ → ENTRADA INVÁLIDA
estado ← q0, caché ← B, registrar ID 0
repetir:
    si estado ∈ F                      → ACEPTADA
    t ← δ(estado, caché, símbolo bajo el cabezal)
    si t no existe                     → RECHAZADA
    si pasos == max_steps              → DETENIDA POR LÍMITE DE PASOS
    escribir t.write_symbol, mover t.move
    estado ← t.next_state, caché ← t.write_cache
    registrar ID
```

El límite se verifica después de buscar la transición, de modo que una máquina que se detiene exactamente en el paso `max_steps` se clasifica correctamente como aceptada o rechazada.

## Máquinas de demostración

### MT reconocedora: L = { aⁿbⁿcⁿ | n ≥ 1 } — [`machines/reconocedora.yaml`](machines/reconocedora.yaml)

Lenguaje que no es libre de contexto, por lo que ningún autómata de pila puede reconocerlo.

- Q = {q0, q1, q2, q3, q4, q5, qf}, Σ = {a, b, c}, Γ = {a, b, c, X, Y, Z, B}, q0 inicial, F = {qf}
- En cada ronda marca una `a` con X, una `b` con Y y una `c` con Z, y regresa a la X. Cuando no quedan `a`, verifica que solo haya Y seguidas de Z hasta el blanco.

| Estado | Función |
|---|---|
| q0 | Marca una `a` con X, o pasa a verificar si lee Y |
| q1 | Avanza sobre `a`/Y hasta la primera `b` y la marca con Y |
| q2 | Avanza sobre `b`/Z hasta la primera `c` y la marca con Z |
| q3 | Regresa a la izquierda hasta la X |
| q4 | Verifica que solo queden Y |
| q5 | Verifica que solo queden Z hasta el blanco |

Transiciones (la caché no se usa, siempre vale B):

| δ | Resultado |
|---|---|
| δ([q0, B], a) | ([q1, B], X, R) |
| δ([q0, B], Y) | ([q4, B], Y, R) |
| δ([q1, B], a) | ([q1, B], a, R) |
| δ([q1, B], Y) | ([q1, B], Y, R) |
| δ([q1, B], b) | ([q2, B], Y, R) |
| δ([q2, B], b) | ([q2, B], b, R) |
| δ([q2, B], Z) | ([q2, B], Z, R) |
| δ([q2, B], c) | ([q3, B], Z, L) |
| δ([q3, B], a) | ([q3, B], a, L) |
| δ([q3, B], b) | ([q3, B], b, L) |
| δ([q3, B], Y) | ([q3, B], Y, L) |
| δ([q3, B], Z) | ([q3, B], Z, L) |
| δ([q3, B], X) | ([q0, B], X, R) |
| δ([q4, B], Y) | ([q4, B], Y, R) |
| δ([q4, B], Z) | ([q5, B], Z, R) |
| δ([q5, B], Z) | ([q5, B], Z, R) |
| δ([q5, B], B) | ([qf, B], B, L) |

Resultados:

| Cadena | Longitud | Resultado | Pasos |
|---|---|---|---|
| `aabbcc` | 6 | ACEPTADA | 23 |
| `aaabbbccc` | 9 | ACEPTADA | 46 |
| `aabbbcc` | 7 | RECHAZADA (sobra una `b`) | 24 |
| `abcabc` | 6 | RECHAZADA (orden incorrecto) | 7 |

### MT alteradora: duplicación w → ww — [`machines/alteradora.yaml`](machines/alteradora.yaml)

Transforma cualquier cadena w ∈ {a, b}* en ww. Usa la caché para transportar cada símbolo hasta el final de la cinta.

- Q = {q0, q1, q2, q3, q4, qf}, Σ = {a, b}, Γ = {a, b, X, Y, P, Q, B}, q0 inicial, F = {qf}
- X/Y marcan los símbolos originales ya copiados (a/b); P/Q son las copias de a/b.

| Estado | Función |
|---|---|
| q0 | Guarda el siguiente símbolo original en la caché y lo marca (a → X, b → Y); si encuentra una copia, pasa a restaurar |
| q1 | Lleva el símbolo de la caché hasta el primer blanco y escribe su copia (a → P, b → Q) |
| q2 | Regresa a la izquierda hasta la última marca |
| q3 | Restaura las copias hacia la derecha (P → a, Q → b) |
| q4 | Restaura las marcas hacia la izquierda (X → a, Y → b) y deja el cabezal al inicio |

Transiciones:

| δ | Resultado | | δ | Resultado |
|---|---|---|---|---|
| δ([q0, B], a) | ([q1, a], X, R) | | δ([q2, B], a) | ([q2, B], a, L) |
| δ([q0, B], b) | ([q1, b], Y, R) | | δ([q2, B], b) | ([q2, B], b, L) |
| δ([q0, B], P) | ([q3, B], P, S) | | δ([q2, B], P) | ([q2, B], P, L) |
| δ([q0, B], Q) | ([q3, B], Q, S) | | δ([q2, B], Q) | ([q2, B], Q, L) |
| δ([q0, B], B) | ([qf, B], B, S) | | δ([q2, B], X) | ([q0, B], X, R) |
| δ([q1, a], a) | ([q1, a], a, R) | | δ([q2, B], Y) | ([q0, B], Y, R) |
| δ([q1, a], b) | ([q1, a], b, R) | | δ([q3, B], P) | ([q3, B], a, R) |
| δ([q1, a], P) | ([q1, a], P, R) | | δ([q3, B], Q) | ([q3, B], b, R) |
| δ([q1, a], Q) | ([q1, a], Q, R) | | δ([q3, B], B) | ([q4, B], B, L) |
| δ([q1, a], B) | ([q2, B], P, L) | | δ([q4, B], a) | ([q4, B], a, L) |
| δ([q1, b], a) | ([q1, b], a, R) | | δ([q4, B], b) | ([q4, B], b, L) |
| δ([q1, b], b) | ([q1, b], b, R) | | δ([q4, B], X) | ([q4, B], a, L) |
| δ([q1, b], P) | ([q1, b], P, R) | | δ([q4, B], Y) | ([q4, B], b, L) |
| δ([q1, b], Q) | ([q1, b], Q, R) | | δ([q4, B], B) | ([qf, B], B, R) |
| δ([q1, b], B) | ([q2, B], Q, L) | | | |

Resultados:

| Cadena | Longitud | Cinta final | Pasos |
|---|---|---|---|
| `abbab` | 5 | `abbababbab` | 73 |
| `aabbb` | 5 | `aabbbaabbb` | 73 |
| `babaa` | 5 | `babaababaa` | 73 |
| `baaaab` | 6 | `baaaabbaaaab` | 99 |

## Pruebas

```bash
python -m pytest
```

| Archivo | Tipo | Qué verifica |
|---|---|---|
| `tests/test_parser.py` | Unitaria | Lectura del YAML, interpretación de transiciones y detección de configuraciones inválidas |
| `tests/test_tape.py` | Unitaria | Inicialización, escritura y movimientos L/R/S de la cinta, incluso fuera de la entrada |
| `tests/test_simulator.py` | Unitaria | Aceptación, rechazo, transiciones inexistentes, uso de la caché, registro de IDs y límite de pasos |
| `tests/test_formatter.py` | Unitaria | Formato de la descripción formal, IDs, configuración final y resumen |
| `tests/test_cli.py` | Integración | Ejecución completa desde la línea de comandos, errores y `--max-steps` |
| `tests/test_machines.py` | Integración | Máquinas de demostración: la reconocedora se compara contra la definición del lenguaje en todas las cadenas sobre {a, b, c} de longitud ≤ 7, y la alteradora produce ww para todas las cadenas sobre {a, b} de longitud ≤ 7 |

## Video de demostración

Enlace al video (YouTube, no listado): _pendiente_
