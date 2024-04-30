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
        self._binance_label = tk.Label(self._commands_frame, text="Binance", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
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

        # creo un diccionario para almacenar las labels que irán en las filas del widget
        self.body_widgets = dict()

        self._headers = ["symbol", "exchange", "bid", "ask", "remove"]

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        for idx, h in enumerate(self._headers):
            # uso el inline if para decir si tiene datos, mostrá el remove, sino ""
            header = tk.Label(self._table_frame, text=h.capitalize() if h != "remove" else "", bg=BG_COLOR, fg=FG_COLOR,
                              font=BOLD_FONT)
            header.grid(row=0, column=idx)

        # itero para completar dinámicamente las etiquetas del widget
        # symbol, exchange, bid, ask
        for h in self._headers:
            self.body_widgets[h] = dict()
            # Aca agrego las variables que alimentarán mas adelante el widget en el método
            # add_symbol() (solo bid y ask, ya que son valores variables)
            if h in ["bid", "ask"]:
                self.body_widgets[h + "_var"] = dict()

        # una variable int que se posiciona en la última fila de la tabla y se irá incrementando a medida
        # que se agregue filas (datos) de ["symbol", "exchange", "bid", "ask"]
        # empieza en 1 porque la fila 0 son los headers mencionados
        self._body_index = 1

    # Lo usamos para remover un symbol de la watchlist
    def _remove_symbol(self, b_index: int):
        # si está en el header, reestructuro el grid con el método grid_forget() y borro la fila con el del
        for h in self._headers:
            self.body_widgets[h][b_index].grid_forget()
            del self.body_widgets[h][b_index]

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

    def _add_symbol(self, symbol: str, exchange: str):
        # cada vez que ejecuto el add_symbol() se incrementa la variable del indice
        b_index = self._body_index

        self.body_widgets['symbol'][b_index] = tk.Label(self._table_frame, text=symbol, bg=BG_COLOR, fg=FG_COLOR_2,
                                                        font=GLOBAL_FONT)
        self.body_widgets['symbol'][b_index].grid(row=b_index, column=0)

        self.body_widgets['exchange'][b_index] = tk.Label(self._table_frame, text=exchange, bg=BG_COLOR, fg=FG_COLOR_2,
                                                          font=GLOBAL_FONT)
        self.body_widgets['exchange'][b_index].grid(row=b_index, column=1)

        # Acá cambio a textVariable , ya que el valor que aparezca ahí va a ser variable (las cotizaciones
        # se irán actualizando en tiempo real, por ello se usar este parámetro
        # El valor de este parámetro, por ello debe ser un tkinter StringVar Object
        self.body_widgets['bid_var'][b_index] = tk.StringVar()

        self.body_widgets['bid'][b_index] = tk.Label(self._table_frame,
                                                     textvariable=self.body_widgets['bid_var'][b_index],
                                                     bg=BG_COLOR, fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT)
        self.body_widgets['bid'][b_index].grid(row=b_index, column=2)

        self.body_widgets['ask_var'][b_index] = tk.StringVar()

        self.body_widgets['ask'][b_index] = tk.Label(self._table_frame,
                                                     textvariable=self.body_widgets['ask_var'][b_index],
                                                     bg=BG_COLOR, fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT)
        self.body_widgets['ask'][b_index].grid(row=b_index, column=3)

        # en el command defino el trigger que se va a ejecutar cuando haga click en el botón de "borrar".
        # acá viene algo IMPORTANTE: Esto dispara un callback method, pero acá tenemos que pasar argumentos,
        # entonces como los callbacks no llevan argumentos, para forzar un callback uso la palabra reservada
        # lambda, adelante del método, para que no se ejecute automaticamente (al tener argumentos) y esperar
        # a tocar el botón para ejecutarse
        self.body_widgets['remove'][b_index] = tk.Button(self._table_frame,
                                                         text="X",
                                                         bg="darkred", fg=FG_COLOR,
                                                         font=GLOBAL_FONT,
                                                         command=lambda: self._remove_symbol(b_index))
        self.body_widgets['remove'][b_index].grid(row=b_index, column=4)

        self._body_index += 1
