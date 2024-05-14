# Este módulo lo agrego para tener un componente con scrolling (una pantalla) donde pueda subir y bajar
# ya que el componente Frame de tkinter no es scrollable, por ello voy a crear un módulo personalizado
import tkinter as tk


class ScrollableFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Seteo el canvas para que quede de esta manera: rectángulo frame, dentro el canvas, dentro el scrollable frame
        # y al costado el vertical scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0, **kwargs)
        # creo el vertical scrollbar
        self.vsb = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        # lo mando dentro del canvas
        self.sub_frame = tk.Frame(self.canvas, **kwargs)

        # le bindeo un callback para que cada vez que haya un cambio (evento configure) se dispare la configuración
        # en la pantalla del sub_frame y quede correctamente mostrado.
        self.sub_frame.bind("<Configure>", self._on_frame_configure)
        # Para identificar cuando entro y salgo del frame
        self.sub_frame.bind("<Enter>", self._activate_mousewheel)
        self.sub_frame.bind("<Leave>", self._deactivate_mousewheel)

        # crea el window subframe dentro del canvas
        # anchor indica que el frame se ubicara en el top left de la ventana (new window)
        # y la tupla (0,0) indica que será al principio del eje x y eje y
        self.canvas.create_window((0,0), window=self.sub_frame, anchor="nw")

        # linkeo el canvas con el vertical scrollbar
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_frame_configure(self, event: tk.Event):
        # bbox all significa todas las coordenadas del contenido del canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _activate_mousewheel(self, event: tk.Event):
        # Cuando entra el mouse en el frame lo activo para permitir scrollear
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _deactivate_mousewheel(self, event: tk.Event):
        # Cuando entra el mouse en el frame lo activo para permitir scrollear
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event):
        # formula para determinar cuanto se mueve el mouse
        self.canvas.yview_scroll(int(-1 * (event.delta / 60)), "units")



