"""Interfaz gráfica (Tkinter) del simulador de Máquinas de Turing.

Uso:
    python interfaz.py
    python interfaz.py machines/reconocedora.yaml
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from turing import DEFAULT_MAX_STEPS, ConfigError, Outcome, collect_warnings, load_machine, simulate, simulate_all
from turing.formatter import (
    format_id_line,
    format_machine,
    format_result_footer,
    format_result_header,
    format_summary,
    format_warnings,
)


class App(tk.Tk):
    def __init__(self, initial_file=None):
        super().__init__()
        self.title("Simulador de Máquinas de Turing")
        self.geometry("1300x700")
        self.machine = None
        self.results = []
        self.source = ""

        self._build_top()
        self._build_panels()

        if initial_file:
            self.load_file(initial_file)

    def _build_top(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=5, pady=5)
        tk.Button(top, text="Cargar máquina (.yaml)", command=self.choose_file).pack(side="left")
        self.file_label = tk.Label(top, text="(ningún archivo cargado)")
        self.file_label.pack(side="left", padx=10)
        self.max_steps = tk.StringVar(value=str(DEFAULT_MAX_STEPS))
        tk.Entry(top, textvariable=self.max_steps, width=10).pack(side="right")
        tk.Label(top, text="Límite de pasos:").pack(side="right")

    def _build_panels(self):
        panels = tk.Frame(self)
        panels.pack(fill="both", expand=True, padx=5, pady=5)
        for col in range(3):
            panels.columnconfigure(col, weight=1, uniform="panel")
        panels.rowconfigure(0, weight=1)

        entrada = tk.LabelFrame(panels, text="Entrada")
        entrada.grid(row=0, column=0, sticky="nsew", padx=2)
        pasos = tk.LabelFrame(panels, text="Pasos")
        pasos.grid(row=0, column=1, sticky="nsew", padx=2)
        resultados = tk.LabelFrame(panels, text="Resultados")
        resultados.grid(row=0, column=2, sticky="nsew", padx=2)

        # Entrada: lista de cadenas, campo para agregar una nueva y descripción de la máquina
        tk.Label(entrada, text="Cadenas de entrada:").pack(anchor="w")
        list_frame = tk.Frame(entrada)
        list_frame.pack(fill="x")
        self.listbox = tk.Listbox(list_frame, height=10, exportselection=False)
        list_scroll = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=list_scroll.set)
        self.listbox.pack(side="left", fill="x", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        add_frame = tk.Frame(entrada)
        add_frame.pack(fill="x", pady=3)
        self.new_input = tk.StringVar()
        entry = tk.Entry(add_frame, textvariable=self.new_input)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self.add_input())
        tk.Button(add_frame, text="Agregar y simular", command=self.add_input).pack(side="right")

        tk.Label(entrada, text="Máquina:").pack(anchor="w")
        self.machine_text = self._make_text(entrada)

        self.steps_text = self._make_text(pasos)
        self.result_text = self._make_text(resultados)

    @staticmethod
    def _make_text(parent):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="none", font=("Courier New", 10), state="disabled")
        yscroll = tk.Scrollbar(frame, command=text.yview)
        xscroll = tk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.config(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(side="bottom", fill="x")
        text.pack(side="left", fill="both", expand=True)
        return text

    @staticmethod
    def _set_text(widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

    def _read_max_steps(self):
        try:
            value = int(self.max_steps.get())
            if value < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El límite de pasos debe ser un entero no negativo.")
            return None
        return value

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar máquina de Turing",
            filetypes=[("Archivos YAML", "*.yaml")],
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        if not path.lower().endswith(".yaml"):
            messagebox.showerror("Error", "Solo se aceptan archivos con extensión .yaml")
            return
        max_steps = self._read_max_steps()
        if max_steps is None:
            return
        try:
            machine = load_machine(path)
        except ConfigError as e:
            messagebox.showerror("Error en el archivo", str(e))
            return
        except OSError as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
            return

        self.machine = machine
        self.source = path
        self.file_label.config(text=os.path.basename(path))
        warnings = format_warnings(collect_warnings(machine))
        self._set_text(self.machine_text, format_machine(machine, path) + ("\n" + warnings if warnings else ""))
        self.results = simulate_all(machine, max_steps)
        self.refresh_list()
        if self.results:
            self.select(0)
        else:
            self._set_text(self.steps_text, "")
            self._set_text(self.result_text, "El archivo no contiene cadenas en 'inputs'.")

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for i, result in enumerate(self.results, 1):
            self.listbox.insert("end", f"{i}. {result.input_word or 'ε'}  [{result.outcome.value}]")

    def add_input(self):
        if self.machine is None:
            messagebox.showinfo("Aviso", "Primero carga un archivo .yaml.")
            return
        max_steps = self._read_max_steps()
        if max_steps is None:
            return
        word = self.new_input.get()
        self.machine.inputs.append(word)
        self.results.append(simulate(self.machine, word, max_steps))
        self.new_input.set("")
        self.refresh_list()
        self.select(len(self.results) - 1)

    def select(self, index):
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.listbox.see(index)
        self.show_result(index)

    def on_select(self, _event):
        selection = self.listbox.curselection()
        if selection:
            self.show_result(selection[0])

    def show_result(self, index):
        result = self.results[index]
        total = len(self.results)
        header = format_result_header(result, index + 1, total)
        if result.outcome is Outcome.INVALID_INPUT:
            self._set_text(self.steps_text, "(sin pasos: la entrada es inválida)")
            self._set_text(self.result_text, header + "\n" + format_summary(self.results))
            return
        width = len(str(result.ids[-1].step))
        steps = "\n".join(format_id_line(desc, i, width) for i, desc in enumerate(result.ids))
        self._set_text(self.steps_text, steps)
        self._set_text(
            self.result_text,
            format_result_footer(result) + "\n" + format_summary(self.results),
        )


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    App(argv[0] if argv else None).mainloop()


if __name__ == "__main__":
    main()
