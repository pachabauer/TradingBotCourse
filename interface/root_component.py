import logging
import tkinter as tk
from interface.styling import *
from interface.logging_component import Logging

from connectors.bitmex_futures import BitmexClient
from connectors.binance_futures import BinanceFuturesClient

from interface.watchlist_component import Watchlist

logger = logging.getLogger()


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

        # Logs

        for log in self.bitmex.logs:
            if not log['displayed']:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log['displayed']:
                self._logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Watchlist prices
        # Uso para

        # Acá voy a mostrar el bid y ask en la interface.
        # Si no está en la interface lo agrego

        try:
            for key, value in self._watchlist_frame.body_widgets['symbol'].items():

                symbol = self._watchlist_frame.body_widgets['symbol'][key].cget('text')
                exchange = self._watchlist_frame.body_widgets['exchange'][key].cget('text')

                if exchange == "Binance":
                    if symbol not in self.binance.contracts:
                        continue

                    if symbol not in self.binance.prices:
                        self.binance.get_bid_ask(self.binance.contracts[symbol])

                    # Lo uso para ajustar el número de decimales y que no salga el valor con notación científica
                    # 1 e-05 (por ejemplo)
                    precision = self.binance.contracts[symbol].price_decimals

                    prices = self.binance.prices[symbol]

                elif exchange == "Bitmex":
                    if symbol not in self.bitmex.contracts:
                        continue

                    if symbol not in self.bitmex.prices:
                        continue

                    precision = self.bitmex.contracts[symbol].price_decimals

                    prices = self.bitmex.prices[symbol]

                else:
                    continue

                # Si está en la interface lo actualizo

                if prices['bid'] is not None:

                    # Uso esta variable para redondear el precio en aquellos contratos con muchos decimales al pedo
                    price_str = "{0:.{prec}f}".format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['bid_var'][key].set(price_str)

                if prices['ask'] is not None:

                    price_str = "{0:.{prec}f}".format(prices['ask'], prec=precision)
                    self._watchlist_frame.body_widgets['ask_var'][key].set(price_str)

        except RuntimeError as e:
            logger.error("Error while looping through watchlist dictionary: %s", e)
        self.after(1500, self._update_ui)
