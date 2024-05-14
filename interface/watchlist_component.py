# Importamos el módulo tkinter y el módulo typing.
# Importamos todo desde el módulo models y las configuraciones de estilo desde interface.styling
import tkinter as tk
import typing
from models import *
from interface.styling import *
from interface.autocomplete_widget import Autocomplete
from interface.scrollable_frame import ScrollableFrame


class Watchlist(tk.Frame):
    # paso una lista de contratos de cada exchange, para que cuando los seleccione en el box, aparezca un listado
    # de ellos y no sea posible agregar o escribir cualquier cosa.

    def __init__(self, binance_contracts: typing.Dict[str, Contract], bitmex_contracts: typing.Dict[str, Contract],
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Se crean listas de símbolos para los contratos de Binance y Bitmex.
        self.binance_symbols = list(binance_contracts.keys())
        self.bitmex_symbols = list(bitmex_contracts.keys())

        # Se crean dos marcos (Frame) para los controles de la interfaz y la tabla de visualización.
        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)
        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        # Se crea una etiqueta para Binance y se coloca en el marco de comandos.
        # es el frame de arriba que se usará para ingresar una crypto y agregarla a la watchlist
        self._binance_label = tk.Label(self._commands_frame, text="Binance", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        # con el grid() especifico, en este caso que irá top left (row=0, column=0)
        self._binance_label.grid(row=0, column=0)

        # Acá ponemos los entry boxes (para ingresar la crypto a buscar y agregar a la watchlist
        # insertbackground es el color del cursor dentro del entry
        self._binance_entry = Autocomplete( self.binance_symbols, self._commands_frame, fg=FG_COLOR, justify=tk.CENTER,
                                            insertbackground=FG_COLOR, bg=BG_COLOR2)

        # bind() nos permite agregar una funcionalidad al entry, en este caso cuando presiono enter, llama al
        # callback _add_binance_symbol
        self._binance_entry.bind("<Return>", self._add_binance_symbol)

        self._binance_entry.grid(row=1, column=0)

        self._bitmex_label = tk.Label(self._commands_frame, text="Bitmex", bg=BG_COLOR, fg=FG_COLOR, font=BOLD_FONT)
        # especifico que ira top left, pero en la segunda columna (column=1)
        self._bitmex_label.grid(row=0, column=1)

        self._bitmex_entry = Autocomplete(self.bitmex_symbols, self._commands_frame, fg=FG_COLOR, justify=tk.CENTER,
                                          insertbackground=FG_COLOR, bg=BG_COLOR2)
        self._bitmex_entry.bind("<Return>", self._add_bitmex_symbol)
        self._bitmex_entry.grid(row=1, column=1)

        # Se crean diccionarios para almacenar widgets y una lista de encabezados.
        self.body_widgets = dict()
        self._headers = ["symbol", "exchange", "bid", "ask", "remove"]

        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        self._col_width = 11

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        # Se crean etiquetas de encabezado y se colocan en la primera fila de la tabla.
        for idx, h in enumerate(self._headers):
            # uso el inline if para decir si tiene datos, mostrá el remove, sino ""
            header = tk.Label(self._headers_frame, text=h.capitalize() if h != "remove" else "", bg=BG_COLOR, fg=FG_COLOR,
                              font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)

        # agrego un label adicional para llevar el width para llevar el scrollbar a la derecha
        header = tk.Label(self._headers_frame, text="", bg=BG_COLOR, fg=FG_COLOR,
                          font=GLOBAL_FONT, width=2)
        header.grid(row=0, column=len(self._headers))

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollableFrame(self._table_frame, bg=BG_COLOR, height=250)
        self._body_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

        # itero para completar dinámicamente las etiquetas del widget
        # symbol, exchange, bid, ask
        # Se inicializan los diccionarios para almacenar widgets y variables.
        for h in self._headers:
            self.body_widgets[h] = dict()
            # Aca agrego las variables que alimentarán mas adelante el widget en el método
            # add_symbol() (solo bid y ask, ya que son valores variables)
            if h in ["bid", "ask"]:
                self.body_widgets[h + "_var"] = dict()

        # una variable int que se posiciona en la última fila de la tabla y se irá incrementando a medida
        # que se agregue filas (datos) de ["symbol", "exchange", "bid", "ask"]
        # empieza en 1 porque la fila 0 son los headers mencionados
        self._body_index = 0

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

        self.body_widgets['symbol'][b_index] = tk.Label(self._body_frame.sub_frame, text=symbol, bg=BG_COLOR,
                                                        fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['symbol'][b_index].grid(row=b_index, column=0)

        self.body_widgets['exchange'][b_index] = tk.Label(self._body_frame.sub_frame, text=exchange, bg=BG_COLOR,
                                                          fg=FG_COLOR_2,font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['exchange'][b_index].grid(row=b_index, column=1)

        # Acá cambio a textVariable , ya que el valor que aparezca ahí va a ser variable (las cotizaciones
        # se irán actualizando en tiempo real, por ello se usar este parámetro
        # El valor de este parámetro, por ello debe ser un tkinter StringVar Object
        self.body_widgets['bid_var'][b_index] = tk.StringVar()

        self.body_widgets['bid'][b_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['bid_var'][b_index],
                                                     bg=BG_COLOR, fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['bid'][b_index].grid(row=b_index, column=2)

        self.body_widgets['ask_var'][b_index] = tk.StringVar()

        self.body_widgets['ask'][b_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['ask_var'][b_index],
                                                     bg=BG_COLOR, fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['ask'][b_index].grid(row=b_index, column=3)

        # en el command defino el trigger que se va a ejecutar cuando haga click en el botón de "borrar".
        # acá viene algo IMPORTANTE: Esto dispara un callback method, pero acá tenemos que pasar argumentos,
        # entonces como los callbacks no llevan argumentos, para forzar un callback uso la palabra reservada
        # lambda, adelante del método, para que no se ejecute automaticamente (al tener argumentos) y esperar
        # a tocar el botón para ejecutarse
        self.body_widgets['remove'][b_index] = tk.Button(self._body_frame.sub_frame,
                                                         text="X",
                                                         bg="darkred", fg=FG_COLOR,
                                                         font=GLOBAL_FONT,
                                                         command=lambda: self._remove_symbol(b_index),
                                                         width=4)
        self.body_widgets['remove'][b_index].grid(row=b_index, column=4)

        self._body_index += 1
