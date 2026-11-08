"""Interfaz gráfica (Tkinter) del simulador de Máquinas de Turing.

Uso:
    python interfaz.py
    python interfaz.py machines/reconocedora.yaml
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox

from turing import DEFAULT_MAX_STEPS, ConfigError, Outcome, collect_warnings, load_machine, simulate, simulate_all
from turing.formatter import (
    format_id_line,
    format_machine,
    format_result_footer,
    format_result_header,
    format_warnings,
)

try:
    from PIL import Image, ImageTk
except ImportError:  # Sin Pillow la interfaz funciona igual, solo sin fotografías.
    Image = ImageTk = None

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
GODEL_PHOTO = "Agregar Archivo.png"
TURING_PHOTO = "Agregar Archivo (3).png"
PHOTO_SIZE = 120

# Paleta: fondo crema, paneles marrón oscuro y cajas de texto casi blancas para el contraste.
BG = "#EADFC8"
HEADER_BG = "#3B2616"
HEADER_FG = "#F6EBD2"
BOX_BG = "#FFFBF0"
BOX_FG = "#24170D"
BORDER = "#5C3D24"
BUTTON_BG = "#8A1C2B"
BUTTON_ACTIVE = "#A62535"
ACCENT = "#E0A94A"

OUTCOME_COLORS = {
    Outcome.ACCEPTED: "#1E6B34",
    Outcome.REJECTED: "#A3201F",
    Outcome.STEP_LIMIT: "#B35C00",
    Outcome.INVALID_INPUT: "#5E5E5E",
}


def _pick_font(root, candidates, fallback):
    available = set(tkfont.families(root))
    return next((name for name in candidates if name in available), fallback)


class App(tk.Tk):
    def __init__(self, initial_file=None):
        super().__init__()
        self.title("Máquina Moderna de Turing")
        self.geometry("1400x820")
        self.configure(bg=BG)
        self.machine = None
        self.results = []
        self.photos = []

        serif = _pick_font(self, ("Georgia", "Palatino Linotype", "Cambria", "Times New Roman"), "serif")
        mono = _pick_font(self, ("Consolas", "Cascadia Mono", "Courier New"), "Courier")
        self.fonts = {
            "title": (serif, 26, "bold"),
            "subtitle": (serif, 12, "italic"),
            "header": (serif, 12, "bold"),
            "button": (serif, 11, "bold"),
            "label": (serif, 11),
            "mono": (mono, 11),
        }

        self._build_banner()
        self._build_toolbar()
        self._build_panels()

        if initial_file:
            self.load_file(initial_file)

    def _load_photo(self, filename):
        path = os.path.join(ASSETS_DIR, filename)
        if ImageTk is None or not os.path.exists(path):
            return None
        image = Image.open(path).convert("RGB")
        side = min(image.size)
        # Recorte cuadrado: Gödel desde la esquina superior izquierda; Turing, a la derecha donde está el rostro.
        left = image.width - side if filename == TURING_PHOTO else 0
        image = image.crop((left, 0, left + side, side)).resize((PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.photos.append(photo)
        return photo

    def _build_banner(self):
        banner = tk.Frame(self, bg=HEADER_BG)
        banner.pack(fill="x")
        banner.columnconfigure(1, weight=1)

        for column, filename, side_pad in ((0, GODEL_PHOTO, (10, 0)), (2, TURING_PHOTO, (0, 10))):
            photo = self._load_photo(filename)
            if photo:
                frame = tk.Frame(banner, bg=ACCENT, padx=3, pady=3)
                frame.grid(row=0, column=column, padx=side_pad, pady=8)
                tk.Label(frame, image=photo, bd=0).pack()

        center = tk.Frame(banner, bg=HEADER_BG)
        center.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            center, text="MÁQUINA MODERNA DE TURING", font=self.fonts["title"], bg=HEADER_BG, fg=HEADER_FG
        ).pack(pady=(22, 0))
        tk.Label(
            center, text="Simulador de máquinas de Turing de una cinta", font=self.fonts["subtitle"],
            bg=HEADER_BG, fg=ACCENT,
        ).pack()
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=10, pady=8)
        self._button(bar, "Agregar archivo (.yaml)", self.choose_file).pack(side="left")
        self.file_label = tk.Label(
            bar, text="(ningún archivo cargado)", font=self.fonts["label"], bg=BG, fg=BOX_FG
        )
        self.file_label.pack(side="left", padx=12)
        self.max_steps = tk.StringVar(value=str(DEFAULT_MAX_STEPS))
        self._entry(bar, self.max_steps, width=10).pack(side="right")
        tk.Label(bar, text="Límite de pasos:", font=self.fonts["label"], bg=BG, fg=BOX_FG).pack(side="right", padx=6)

    def _build_panels(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=2, uniform="col")
        body.columnconfigure(1, weight=3, uniform="col")
        body.columnconfigure(2, weight=3, uniform="col")
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=2)
        left.rowconfigure(1, weight=3)

        entrada = self._panel(left, "Cadenas de entrada:", row=0, column=0, pady=(0, 6))
        list_frame = tk.Frame(entrada, bg=BOX_BG)
        list_frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            list_frame, exportselection=False, font=self.fonts["mono"], bg=BOX_BG, fg=BOX_FG, bd=0,
            highlightthickness=0, selectbackground=HEADER_BG, selectforeground=HEADER_FG, activestyle="none",
        )
        list_scroll = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        add_frame = tk.Frame(entrada, bg=BG)
        add_frame.pack(fill="x", pady=(6, 0))
        self.new_input = tk.StringVar()
        entry = self._entry(add_frame, self.new_input)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry.bind("<Return>", lambda _e: self.add_input())
        self._button(add_frame, "Simular", self.add_input).pack(side="right")

        maquina = self._panel(left, "Máquina:", row=1, column=0)
        self.machine_text = self._make_text(maquina)

        pasos = self._panel(body, "Pasos:", row=0, column=1, padx=6)
        self.steps_text = self._make_text(pasos)

        resultados = self._panel(body, "Resultado:", row=0, column=2, padx=(6, 0))
        self.result_text = self._make_text(resultados)

    def _panel(self, parent, title, **grid):
        outer = tk.Frame(parent, bg=BORDER, padx=2, pady=2)
        outer.grid(sticky="nsew", **grid)
        tk.Label(
            outer, text=title, font=self.fonts["header"], bg=HEADER_BG, fg=HEADER_FG, anchor="w", padx=8, pady=4
        ).pack(fill="x")
        inner = tk.Frame(outer, bg=BG, padx=6, pady=6)
        inner.pack(fill="both", expand=True)
        return inner

    def _button(self, parent, text, command):
        return tk.Button(
            parent, text=text, command=command, font=self.fonts["button"], bg=BUTTON_BG, fg=HEADER_FG,
            activebackground=BUTTON_ACTIVE, activeforeground=HEADER_FG, relief="flat", bd=0,
            padx=14, pady=6, cursor="hand2",
        )

    def _entry(self, parent, variable, width=20):
        return tk.Entry(
            parent, textvariable=variable, width=width, font=self.fonts["mono"], bg=BOX_BG, fg=BOX_FG,
            insertbackground=BOX_FG, relief="solid", bd=1, highlightthickness=0,
        )

    def _make_text(self, parent):
        frame = tk.Frame(parent, bg=BOX_BG, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True)
        text = tk.Text(
            frame, wrap="none", font=self.fonts["mono"], bg=BOX_BG, fg=BOX_FG, bd=0, highlightthickness=0,
            padx=8, pady=6, state="disabled",
        )
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
        self.file_label.config(text=os.path.basename(path))
        warnings = format_warnings(collect_warnings(machine))
        self._set_text(
            self.machine_text,
            format_machine(machine, with_title=False) + ("\n" + warnings if warnings else ""),
        )
        self.results = simulate_all(machine, max_steps)
        self.refresh_list()
        if self.results:
            self.select(0)
        else:
            self._set_text(self.steps_text, "")
            self._set_text(self.result_text, "El archivo no contiene cadenas en 'inputs'.")

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for i, result in enumerate(self.results):
            self.listbox.insert("end", f"{i + 1}. {result.input_word or 'ε'}  [{result.outcome.value}]")
            self.listbox.itemconfig(i, fg=OUTCOME_COLORS[result.outcome])

    def add_input(self):
        if self.machine is None:
            messagebox.showinfo("Aviso", "Primero agrega un archivo .yaml.")
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
        if result.outcome is Outcome.INVALID_INPUT:
            header = format_result_header(result, index + 1, len(self.results))
            self._set_text(self.steps_text, "(sin pasos: la entrada es inválida)")
            self._set_text(self.result_text, header)
            return
        width = len(str(result.ids[-1].step))
        steps = "\n".join(format_id_line(desc, i, width) for i, desc in enumerate(result.ids))
        self._set_text(self.steps_text, steps)
        self._set_text(self.result_text, format_result_footer(result))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    App(argv[0] if argv else None).mainloop()


if __name__ == "__main__":
    main()
