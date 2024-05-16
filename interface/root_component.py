import logging
import tkinter as tk
from tkinter.messagebox import askquestion
from interface.styling import *
from interface.logging_component import Logging

from connectors.bitmex_futures import BitmexClient
from connectors.binance_futures import BinanceFuturesClient
from interface.trades_component import TradesWatch
from interface.watchlist_component import Watchlist
from interface.strategy_component import StrategyEditor

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
        # Uso este protocolo para terminar el programa (detener todos los threads) al cerrar la ventana del bot
        # y llamo al callback para hacerlo
        self.protocol("WM_DELETE_WINDOW", self._ask_before_close)

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

        # Cambié el estado para hacerlas públicas y poder usar el self.logging_frame desde otro módulo
        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self.logging_frame.pack(side=tk.TOP)

        self._strategy_frame = StrategyEditor(self, self.binance, self.bitmex, self._right_frame, bg=BG_COLOR)
        self._strategy_frame.pack(side=tk.TOP)

        # Agrego el frame que llevará el trades_component
        self._trades_frame = TradesWatch(self._right_frame, bg=BG_COLOR)
        self._trades_frame.pack(side=tk.TOP)

        self._update_ui()

    def _ask_before_close(self):
        result = askquestion("Confirmation", "Do you really want to exit the application?")
        if result == "yes":
            self.binance.reconnect = False
            self.bitmex.reconnect = False
            self.binance.ws.close()
            self.bitmex.ws.close()

            self.destroy()

    # cada vez que hay un update de información, se ejecutará el update, para actualizar los precios y tenerlos a mano
    # si el log no está en la lista, lo agrega y cada vez que se actualiza el precio, lo agrega a continuación
    # el self.after es para re-ejecutar el update_ui, pero no lleva ()
    def _update_ui(self):

        # Logs

        for log in self.bitmex.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Trades and logs
        # Itero para agregar los logs a la interface de los trades que voy abriendo posición.
        for client in [self.binance, self.bitmex]:
            try:
                for b_index, strat in client.strategies.items():
                    for log in strat.logs:
                        if not log['displayed']:
                            self.logging_frame.add_log(log['log'])
                            log['displayed'] = True

                    # agrego al trade a la interface si está en strat.trades
                    for trade in strat.trades:
                        if trade.time not in self._trades_frame.body_widgets['symbol']:
                            self._trades_frame.add_trade(trade)
                        # si el trade ya está agregado en la interface, puedo hacer update del pnl, etc
                        if trade.contract.exchange == "binance":
                            precision = trade.contract.price_decimals
                        else:
                            # Bitmex siempre muestra los saldos en bitcoin (por eso 8 decimales)
                            precision = 8

                        # muestra el pnl en la interface con formato
                        pnl_str = "{0:.{prec}f}".format(trade.pnl,prec=precision)

                        self._trades_frame.body_widgets['pnl_var'][trade.time].set(pnl_str)
                        self._trades_frame.body_widgets['status_var'][trade.time].set(trade.status.capitalize())

            except RuntimeError as e:
                logger.error("Error while looping through strategies dictionary: %s", e)

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
