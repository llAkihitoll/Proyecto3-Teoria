# Proyecto 3 — Simulador de Máquinas de Turing

Simulador de Máquinas de Turing (MT) **de una cinta** para el curso de Teoría de la Computación.

### Miembros:
- Arturo Lima - 24683
- Saul Castillo - 24915
- Esteban Gonzalez - 24005

### Fotografía del funcionamiento del programa: 
<img width="1917" height="1135" alt="image" src="https://github.com/user-attachments/assets/3a3be991-a78d-461d-91d3-c709714260bc" />


### Video de demostración y explicación del programa:
[Ver video en YouTube](https://youtu.be/_DnWehDj7uM)

El programa:

1. Lee la descripción formal de una MT desde un archivo YAML.
2. Simula cada cadena de entrada configurada en ese archivo.
3. Muestra todas las descripciones instantáneas (IDs) de la simulación.
4. Muestra la configuración final de la cinta.
5. Indica si cada cadena fue **aceptada** o **rechazada**.

## Requisitos

- Python 3.9 o superior (probado con Python 3.13 y 3.14)
- PyYAML (para leer los archivos de configuración)
- pytest (solo para ejecutar las pruebas)

## Como iniciar 

```bash
git clone https://github.com/llAkihitoll/Proyecto3-Teoria.git
cd Proyecto3-Teoria
pip install -r requirements.txt
```

### Interfaz gráfica (Tkinter)

```bash
python interfaz.py [archivo.yaml]
```

Máquinas incluidas:

```bash
python main.py machines/reconocedora.yaml   # MT reconocedora de a^n b^n c^n
python main.py machines/alteradora.yaml     # MT alteradora w -> ww
python main.py machines/godel.yaml          # MT de codificación binaria de Gödel (modo: godel)
python main.py machines/ejemplo_pdf.yaml    # ejemplo literal del enunciado
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


### Etiqueta de reglas `modo`

Una clave opcional al inicio del archivo, antes de `mt`, selecciona las reglas de la máquina:

| `modo` | Reglas |
|---|---|
| `estandar` (por defecto, si se omite) | Las descritas arriba: transiciones con caché `[q, c]` |
| `godel` | Transiciones **sin caché** (`read: x`, `write: y`, es decir δ(q, x) = (p, y, D)); Σ debe ser exactamente `{0, S, (, ), +, =, *, -, /, ^}`; los símbolos fuera de Σ **no** se descartan antes de simular: la propia MT los rechaza al no tener transición. Las IDs se muestran como `[q]` |

```yaml
modo: godel
mt:
  ...
  transitions:
    - {state: v0, read: S, write: S, move: R, next: vS}
```

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
│   ├── godel.yaml
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

### MT de codificación de Gödel en binario — [`machines/godel.yaml`](machines/godel.yaml)

Máquina con `modo: godel` que codifica expresiones de Peano como un número binario, sin potencias de primos: cada símbolo se reemplaza por un bloque de **cuatro bits** y se antepone un `1`.

| Símbolo | `0` | `S` | `(` | `)` | `+` | `=` | `*` | `-` | `/` | `^` |
|---|---|---|---|---|---|---|---|---|---|---|
| Código | 0001 | 0010 | 0011 | 0100 | 0101 | 0110 | 0111 | 1000 | 1001 | 1010 |

Por ejemplo, `S(0)+S(0)` produce `1001000110001010001010010001100010100`. Los operadores `*`, `-`, `/` y `^` solo se codifican, nunca se evalúan. Fases:

1. **Validación** (`v*`, `w*`, `b*`, `bF`, `bG`, `qE1`, `qRet0`, `rR`): acepta solo la gramática `N := 0 | S(N)`, `Suma := N (Op N)*` con `Op ∈ {+, -, *, /, ^}`, `Expr := Suma | Suma = Suma`. Rechaza paréntesis incorrectos, operadores mal colocados, más de un `=` y símbolos desconocidos. Los estados `v*`/`w*` revisan la adyacencia antes/después del `=`, y `b*` empareja cada `S` con un `)` (marcas `Y`/`Z`, restauradas por `rR`). Al terminar escribe `#1` a la derecha y deja el cabezal al inicio.
2. **Codificación** (`e0`, `t_*`, `w_xyz`, `u_yz`, `z_z`, `r1`, `r2`): `e0` marca con `X` el primer símbolo sin procesar y pasa a un estado de viaje propio de ese símbolo (la memoria está en el estado). Este avanza al primer blanco y escribe el primer bit; los estados compartidos `w_xyz`, `u_yz` y `z_z` escriben los otros tres. `r1` y `r2` regresan a la última `X`. Al encontrar `#` lo borra y pasa a la limpieza.
3. **Limpieza** (`c1`, `c2`, `qf`): `c1` borra las `X` hacia la izquierda y `c2` avanza por los blancos hasta el prefijo `1`, donde acepta en `qf`. La cinta queda solo con el número de Gödel y el cabezal sobre su primer `1`.
