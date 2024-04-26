import tkinter as tk
from datetime import datetime
from interface.styling import *


class Logging(tk.Frame):
    # *args significa que puedo pasar argumentos sin especificar su nombre por ejemplo Logging(self._left_frame
    # **kwargs significa que podemos pasar keywords argumentos, por ejemplo dentro del Logging el bg=
    # self._logging_frame = Logging(self._left_frame, bg=BG_COLOR)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # utilidad de tk para mostrar texto, en este caso de logging.
        # el state se refiere a que no podré interactuar como usuario desde la interfaz con el widget (como un
        # solo lectura si está en DISABLED)
        self.logging_text = tk.Text(self, height=10, width=60, state=tk.DISABLED, bg=BG_COLOR, fg=FG_COLOR_2,
                                    font=GLOBAL_FONT)
        # usa pack porque la estructura de la interface no es compleja, entonces no le hace falta usar grid()
        self.logging_text.pack(side=tk.TOP)

    # para agregar un log a la interface
    def add_log(self, message: str):
        # Acá, para escribir el log, primero lo activo
        self.logging_text.configure(state=tk.NORMAL)

        # Uso el insert para agregar el mensaje , el 1.0 significa "al principio"
        # le agrego la hora (tambien puedo usar now() en vez de utcnow(). %a es Mond (de Monday) y los :: son para
        # separar espacios, no es obligatorio.
        self.logging_text.insert("1.0", datetime.utcnow().strftime("%a %H:%M:%S ::") + message + "\n")

        self.logging_text.configure(state=tk.DISABLED)
