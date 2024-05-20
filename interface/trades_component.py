import tkinter as tk
import typing
import datetime
from models import *
from interface.styling import *
from interface.scrollable_frame import ScrollableFrame


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

        self._col_width = 12
        # agrego el scrollable subframe personalizado
        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        # Se crean etiquetas de encabezado y se colocan en la primera fila de la tabla.
        for idx, h in enumerate(self._headers):
            # uso el inline if para decir si tiene datos, mostrá el remove, sino ""
            # cambio a global_font sino causa problemas de display con el nuevo frame
            header = tk.Label(self._headers_frame, text=h.capitalize(), bg=BG_COLOR, fg=FG_COLOR,
                              font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)

        header = tk.Label(self._headers_frame, text="", bg=BG_COLOR, fg=FG_COLOR,
                          font=GLOBAL_FONT, width=2)
        header.grid(row=0, column=len(self._headers))

        # anchor indica que el frame se ubicara en el top left de la ventana (new window)
        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollableFrame(self, bg=BG_COLOR, height=250)
        self._body_frame.pack(side=tk.TOP, anchor="nw", fill=tk.X)


        # itero para completar dinámicamente las etiquetas del widget
        # symbol, exchange, bid, ask
        # Se inicializan los diccionarios para almacenar widgets y variables.
        for h in self._headers:
            self.body_widgets[h] = dict()
            # Aca agrego las variables que alimentarán mas adelante el widget en el método
            # add_symbol() (solo bid y ask, ya que son valores variables)
            if h in ["status", "pnl", "quantity"]:
                self.body_widgets[h + "_var"] = dict()

        self._body_index = 0

    def add_trade(self, trade: Trade):

        b_index = self._body_index

        t_index = trade.time

        dt_str = datetime.datetime.fromtimestamp(trade.time / 1000).strftime("%b %d %H:%M")

        self.body_widgets['time'][t_index] = tk.Label(self._body_frame.sub_frame, text=dt_str, bg=BG_COLOR,
                                                      fg=FG_COLOR_2,font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['time'][t_index].grid(row=b_index, column=0)

        self.body_widgets['symbol'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.contract.symbol,
                                                        bg=BG_COLOR, fg=FG_COLOR_2,font=GLOBAL_FONT
                                                        , width=self._col_width)
        self.body_widgets['symbol'][t_index].grid(row=b_index, column=1)

        self.body_widgets['exchange'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                          text=trade.contract.exchange.capitalize(),
                                                          bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT
                                                          , width=self._col_width)
        self.body_widgets['exchange'][t_index].grid(row=b_index, column=2)

        self.body_widgets['strategy'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.strategy, bg=BG_COLOR,
                                                          fg=FG_COLOR_2,
                                                          font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['strategy'][t_index].grid(row=b_index, column=3)

        self.body_widgets['side'][t_index] = tk.Label(self._body_frame.sub_frame, text=trade.side.capitalize(),
                                                      bg=BG_COLOR,fg=FG_COLOR_2,font=GLOBAL_FONT
                                                      , width=self._col_width)
        self.body_widgets['side'][t_index].grid(row=b_index, column=4)

        # Quantity

        # Variable because the order is not always filled immediately
        self.body_widgets['quantity_var'][t_index] = tk.StringVar()
        self.body_widgets['quantity'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                          textvariable=self.body_widgets['quantity_var'][t_index],
                                                          bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                          width=self._col_width)
        self.body_widgets['quantity'][t_index].grid(row=b_index, column=5)

        self.body_widgets['status_var'][t_index] = tk.StringVar()
        self.body_widgets['status'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                        textvariable=self.body_widgets['status_var'][t_index],
                                                        bg=BG_COLOR, fg=FG_COLOR_2,
                                                        font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['status'][t_index].grid(row=b_index, column=6)

        self.body_widgets['pnl_var'][t_index] = tk.StringVar()
        self.body_widgets['pnl'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['pnl_var'][t_index],
                                                     bg=BG_COLOR,
                                                     fg=FG_COLOR_2,
                                                     font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['pnl'][t_index].grid(row=b_index, column=7)

        self._body_index += 1
