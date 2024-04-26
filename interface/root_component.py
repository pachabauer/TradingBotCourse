import tkinter as tk
from interface.styling import *
from interface.logging_component import Logging

from connectors.bitmex_futures import BitmexClient
from connectors.binance_futures import BinanceFuturesClient

from interface.watchlist_component import Watchlist

# Creo un root component que se utilizará para crear la interface del usuario de la aplicación.
# hago que herede de tk.Tk
# Para poder hacer que herede, aparte de mencionarlo debo llamar al super().__init__()
class Root(tk.Tk):
    def __init__(self, binance: BinanceFuturesClient, bitmex: BitmexClient):
        super().__init__()

        self.binance = binance
        self.bitmex = bitmex

        self.title("Trading Bot")
        # Configuro el background color
        self.configure(bg=BG_COLOR)
        # La idea es tener 4 frames. UP (LEFT RIGHT) Y DOWN (LEFT RIGHT) para poder ubicar 4 funcionalidades a la vista
        # de la interface. A continuación, se configuran de esta manera:
        # tk.Frame(self, se refiere a root (a él mismo))
        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        # indico la ubicación del frame
        self._left_frame.pack(side=tk.LEFT)

        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        # indico la ubicación del frame
        self._right_frame.pack(side=tk.LEFT)

        # Agrego el frame que llevará el watchlist
        self._watchlist_frame = Watchlist(self.binance.contracts, self.bitmex.contracts, self._left_frame, bg=BG_COLOR)
        self._watchlist_frame.pack(side=tk.TOP)

        self._logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self._logging_frame.pack(side=tk.TOP)

        self._update_ui()

    # cada vez que hay un update de información, se ejecutará el update, para actualizar los precios y tenerlos a mano
    # si el log no está en la lista, lo agrega y cada vez que se actualiza el precio, lo agrega a continuación
    # el self.after es para re-ejecutar el update_ui, pero no lleva ()
    def _update_ui(self):
        for log in self.bitmex.logs:
            if not log['displayed']:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log['displayed']:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        self.after(1500, self._update_ui)
