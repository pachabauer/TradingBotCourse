import tkinter as tk
import typing


# usaré esta clase para ofrecer el autocompletar de los símbolos de los contratos en los Entry objects que
# use el usuario
class Autocomplete(tk.Entry):
    def __init__(self, symbols: typing.List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._symbols = symbols
        # Creo el listbox en blanco
        self._lb: tk.Listbox
        # Establezco un boolean para que no se cree un listbox cada vez que presione una key
        self._lb_open = False

        # Acá meto un callback function para poder usar las teclas up y down del teclado para subir y bajar
        # y seleccionar tickers
        self.bind("<Up>", self._up_down)
        self.bind("<Down>", self._up_down)
        self.bind("<Right>", self._select)

        # voy a ir siguiendo lo que vaya escribiendo el usuario con esta variable Stringvar
        self._var = tk.StringVar()
        self.configure(textvariable=self._var)
        # "w" es que dispara el callback method cuando "w" (write). Entonces cada vez que escriba, aparecerá el
        # desplegable "sugiriendo"
        self._var.trace("w", self._changed)

    # método callback que se ejecuta cada vez que presiono una tecla
    def _changed(self, var_name: str, index: str, mode: str):

        self._var.set(self._var.get().upper())

        # Si había símbolos agregados y los borro , desaparece el Listbox (o si no hay ningún elemento).
        if self._var.get() == "":
            if self._lb_open:
                self._lb.destroy()
                self._lb_open = False

        else:
            if not self._lb_open:
                self._lb = tk.Listbox(height=8)
                self._lb.place(x=self.winfo_x() + self.winfo_width(), y=self.winfo_y() + self.winfo_height() + 10)
                self._lb_open = True

            # lista de símbolos que coinciden con las letras que comienzo a escribir
            symbols_matched = [symbol for symbol in self._symbols if symbol.startswith(self._var.get())]

            if len(symbols_matched) > 0:

                try:
                    self._lb.delete(0, tk.END)
                except tk.TclError:
                    pass

                # inserto los símbolos que van coincidiendo en la listbox
                for symbol in symbols_matched[:8]:
                    self._lb.insert(tk.END, symbol)

            else:
                if self._lb_open:
                    self._lb.destroy()
                    self._lb_open = False

    def _select(self, event: tk.Event):
        if self._lb_open:
            self._var.set(self._lb.get(tk.ACTIVE))
            self._lb.destroy()
            self._lb_open = False
            self.icursor(tk.END)

    def _up_down(self, event: tk.Event):

        if self._lb_open:
            # tomá el index de la selección
            # si es igual a vacio ==() lo pongo en -1 para que no tome nada
            if self._lb.curselection() == ():
                index = -1
            else:
                # Elijo el primera (ya que esto devuelve una tupla con varios)
                index = self._lb.curselection()[0]

            lb_size = self._lb.size()

            if index > 0 and event.keysym == "Up":
                self._lb.select_clear(first=index)
                index = str(index - 1)
                self._lb.selection_set(first=index)
                self._lb.activate(index)
            elif index < lb_size - 1 and event.keysym == "Down":
                self._lb.select_clear(first=index)
                index = str(index + 1)
                self._lb.selection_set(first=index)
                self._lb.activate(index)
