import tkinter as tk
import typing

from models import *
from interface.styling import *

class Watchlist(tk.Frame):
    # paso una lista de contratos de cada exchange, para que cuando los seleccione en el box, aparezca un listado
    # de ellos y no sea posible agregar o escribir cualquier cosa.
    def __init__(self, binance_contracts: typing.Dict[str, Contract], bitmex_contracts: typing.Dict[str, Contract],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.binance_symbols = list(binance_contracts.keys())
        self.bitmex_symbols = list(bitmex_contracts.keys())

        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)

        # es el frame de abajo que se usará para mostrar la crypto agregada a la watchlist
        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        # es el frame de arriba que se usará para ingresar una crypto y agregarla a la watchlist
        self._binance_label = tk.Label(self._commands_frame, text= "Binance", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        # con el grid() especifico, en este caso que irá top left (row=0, column=0)
        self._binance_label.grid(row=0, column=0)

        # Acá ponemos los entry boxes (para ingresar la crypto a buscar y agregar a la watchlist
        # insertbackground es el color del cursor dentro del entry
        self._binance_entry = tk.Entry(self._commands_frame, fg=FG_COLOR, justify=tk.CENTER, insertbackground=FG_COLOR,
                                       bg=BG_COLOR2)

        # bind() nos permite agregar una funcionalidad al entry, en este caso cuando presiono enter, llama al
        # callback _add_binance_symbol
        self._binance_entry.bind("<Return>", self._add_binance_symbol)

        self._binance_entry.grid(row=1, column=0)

        self._bitmex_label = tk.Label(self._commands_frame, text="Bitmex", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        # especifico que ira top left, pero en la segunda columna (column=1)
        self._bitmex_label.grid(row=0, column=1)

        self._bitmex_entry = tk.Entry(self._commands_frame, fg=FG_COLOR, justify=tk.CENTER, insertbackground=FG_COLOR,
                                      bg=BG_COLOR2)
        self._bitmex_entry.bind("<Return>", self._add_bitmex_symbol)
        self._bitmex_entry.grid(row=1, column=1)

        self._headers = ["symbol", "exchange", "bid", "ask"]

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        for idx, h in enumerate(self._headers):
            header = tk.Label(self._table_frame, text=h.capitalize(), bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
            header.grid(row=0, column=idx)


    # recibe información del widget (por ejemplo el entry box) y de él sacará información (get)
    def _add_binance_symbol(self, event):
        symbol = event.widget.get()

        # Si el símbolo se encuentra en el listado de contratos, permite avanzar con el enter, agregarlo a la
        # watchlist y borra el texto del box entry. Si , por el contrario, mandamos cualquier símbolo que no
        # existe, no borrará ni agregará a la watchlist.
        if symbol in self.binance_symbols:
            self._add_symbol(symbol, "Binance")
            # Tras completar el símbolo, se borra el box
            event.widget.delete(0, tk.END)

    def _add_bitmex_symbol(self, event):
        symbol = event.widget.get()

        if symbol in self.bitmex_symbols:
            self._add_symbol(symbol, "Bitmex")
            # Tras completar el símbolo, se borra el box
            event.widget.delete(0, tk.END)

    def _add_symbol(self, symbol: str, exchage: str):
        pass
