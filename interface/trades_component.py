import tkinter as tk
import typing
from models import *
from interface.styling import *


class TradesWatch(tk.Frame):
    # En el constructor __init__, se reciben dos diccionarios binance_contracts y bitmex_contracts que representan
    # contratos de Binance y Bitmex respectivamente.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # se usa para referenciar los widgets o labels que hay en cada fila
        self.body_widgets = dict()

        self._headers = ["time", "symbol", "exchange", "strategy", "side", "quantity", "status", "pnl"]

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        # Se crean etiquetas de encabezado y se colocan en la primera fila de la tabla.
        for idx, h in enumerate(self._headers):
            # uso el inline if para decir si tiene datos, mostrá el remove, sino ""
            header = tk.Label(self._table_frame, text=h.capitalize(), bg=BG_COLOR, fg=FG_COLOR,
                              font=BOLD_FONT)
            header.grid(row=0, column=idx)

        # itero para completar dinámicamente las etiquetas del widget
        # symbol, exchange, bid, ask
        # Se inicializan los diccionarios para almacenar widgets y variables.
        for h in self._headers:
            self.body_widgets[h] = dict()
            # Aca agrego las variables que alimentarán mas adelante el widget en el método
            # add_symbol() (solo bid y ask, ya que son valores variables)
            if h in ["status", "pnl"]:
                self.body_widgets[h + "_var"] = dict()

        self._body_index = 1


    def add_trade(self, data: typing.Dict):

        b_index = self._body_index

        t_index = data['time']

        self.body_widgets['time'][t_index] = tk.Label(self._table_frame, text=data['time'], bg=BG_COLOR, fg=FG_COLOR_2,
                                                      font=GLOBAL_FONT)
        self.body_widgets['time'][t_index].grid(row=b_index, column=0)

        self.body_widgets['symbol'][t_index] = tk.Label(self._table_frame, text=data['symbol'], bg=BG_COLOR, fg=FG_COLOR_2,
                                                      font=GLOBAL_FONT)
        self.body_widgets['symbol'][t_index].grid(row=b_index, column=1)

        self.body_widgets['exchange'][t_index] = tk.Label(self._table_frame, text=data['exchange'], bg=BG_COLOR,
                                                        fg=FG_COLOR_2,
                                                        font=GLOBAL_FONT)
        self.body_widgets['exchange'][t_index].grid(row=b_index, column=2)

        self.body_widgets['strategy'][t_index] = tk.Label(self._table_frame, text=data['strategy'], bg=BG_COLOR,
                                                          fg=FG_COLOR_2,
                                                          font=GLOBAL_FONT)
        self.body_widgets['strategy'][t_index].grid(row=b_index, column=3)

        self.body_widgets['side'][t_index] = tk.Label(self._table_frame, text=data['side'], bg=BG_COLOR,
                                                          fg=FG_COLOR_2,
                                                          font=GLOBAL_FONT)
        self.body_widgets['side'][t_index].grid(row=b_index, column=4)

        self.body_widgets['quantity'][t_index] = tk.Label(self._table_frame, text=data['quantity'], bg=BG_COLOR,
                                                      fg=FG_COLOR_2,
                                                      font=GLOBAL_FONT)
        self.body_widgets['quantity'][t_index].grid(row=b_index, column=5)


        self.body_widgets['status_var'][t_index] = tk.StringVar()
        self.body_widgets['status'][t_index] = tk.Label(self._table_frame,
                                                        textvariable= self.body_widgets['status'][t_index],
                                                        bg=BG_COLOR, fg=FG_COLOR_2,
                                                        font=GLOBAL_FONT)
        self.body_widgets['status'][t_index].grid(row=b_index, column=6)

        self.body_widgets['pnl_var'][t_index] = tk.StringVar()
        self.body_widgets['pnl'][t_index] = tk.Label(self._table_frame,
                                                     textvariable= self.body_widgets['pnl_var'][t_index],
                                                     bg=BG_COLOR,
                                                     fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT)
        self.body_widgets['pnl'][t_index].grid(row=b_index, column=7)


        self._body_index +=1




