import logging
import time

import pandas as pd
from typing import *
from models import *
from threading import Timer

# TYPE_CHECKING es una variable que inicializa en False y que evita un error de importación circular
# Ya que en el modulo de strategy_component, que ya se usar en este módulo, ya importamos los connectores,
# pero al querer usarlos aca debemos importarlos, entonces si lo hacemos de la forma habitual, arroja un error
# circular. Pero poniendo el TYPE_CHECKING, evitamos este error, ya que al encontrarlos en otro módulo, los podremos
# usar en este, pero sin importarlos acá mismo
if TYPE_CHECKING:
    from connectors.bitmex_futures import BitmexClient
    from connectors.binance_futures import BinanceFuturesClient

logger = logging.getLogger()

# Creo la variable global TF_EQUIV (timeframe equivalent) para representar los tf en milisegundos
TF_EQUIV = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}


# Clase base de cualquier estrategia que tenga el TradingBot
class Strategy:
    # Agrego el Union y las opciones van entre "" para poder usarlas, debido al TYPE_CHECKING
    # Agrego el nombre de la estrategia como parámetro para pasarlo dentro del objeto nuevo creado en models Trade
    # que pide guardar la estrategia en el nuevo trade
    def __init__(self, client: Union["BitmexClient", "BinanceFuturesClient"], contract: Contract, exchange: str,
                 timeframe: str, balance_pct: float, take_profit: float, stop_loss: float, strat_name):

        # Atributos comunes a cualquier estrategia del TradingBot
        self.client = client
        self.contract = contract
        self.exchange = exchange
        self.tf = timeframe
        self.tf_equiv = TF_EQUIV[timeframe] * 1000  # convierto a milisegundos
        self.balance_pct = balance_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.stat_name = strat_name

        self.ongoing_position = False

        # Cada vez que creo una estrategia traigo las candles del contrato que voy a operar
        self.candles: List[Candle] = []

        self.trades: List[Trade] = []

        # agregare una lista de logs al logging_frame
        self.logs = []

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})

    # creo un método para parsear la información del trade (precio, quantity, stop, etc)
    def parse_trades(self, price: float, size: float, timestamp: int) -> str:

        # Creo el timestamp_diff y el if condicional para no empezar a pasar trades a lo loco y que todo el sistema
        # de updates candles se ralentice y se haga imposible de operar por los delays. Le establezco al menos 2
        # segundos entre trades.
        timestamp_diff = int(time.time() * 1000) - timestamp
        if timestamp_diff >= 2000:
            logger.warning("%s %s: %s milliseconds of difference between the current time and the trade time",
                           self.exchange, self.contract.symbol, timestamp_diff)

        last_candle = self.candles[-1]

        # A su vez este método tendrá 3 posibilidades:

        # Hacer update de nuevos valores de un candle
        # definamos que estamos en un timeframe de 30m, es decir 1800 segundos
        # esto sería si el timestamp de la candle es 1020, quiere decir que estamos en el candle, ya que va
        # de 0 a 1800 (30m en segundos) + los milisegundos y sigue en la misma candle, haremos el update
        if timestamp < last_candle.timestamp + self.tf_equiv:

            last_candle.close = price
            last_candle.volume += size
            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price

            # Agrego para chequear take profit o stop loss
            for trade in self.trades:
                if trade.status == "open" and trade.entry_price is not None:
                    self._check_tp_sl(trade)

            return "same_candle"

        # Comenzar un nuevo candle, pero luego de algunas candles perdidas (por contratos con nulo volumen
        # en determinados timeframes)
        # definamos que estamos en un timeframe de 30m, es decir 1800 segundos
        # esto sería si el timestamp de la candle es 4000, quiere decir que estamos en el candle, ya que va
        # de 0 a 1800 (30m en segundos) + los milisegundos y es en otra candle siguiente a la próxima (1800 a 3600).
        # significa que hemos perdido la 2a candle
        elif timestamp >= last_candle.timestamp + 2 * self.tf_equiv:

            # debo calcular cuántas candles perdi
            # resto el timestamp actual y el de la última candle y divido por el tiempo en milisegundos para tener la
            # cantidad de candles
            # ejemplo: tf 1h (3600) timestamp actual 20000, last_candle timestamp = 3600.
            # 4,55 si lo paso a int = 5 , menos 1 = 4. Perdí 4 velas. es correcto.
            missing_candles = int((timestamp - last_candle.timestamp) / self.tf_equiv) - 1

            logger.info("%s missing %s candles for %s %s (%s %s)", self.exchange, missing_candles, self.contract.symbol,
                        self.tf, timestamp, last_candle.timestamp)

            # agrego las candles perdidas
            for missing in range(missing_candles):
                new_ts = last_candle.timestamp + self.tf_equiv
                candle_info = {'ts': new_ts, 'open': last_candle.close, 'high': last_candle.close,
                               'low': last_candle.close, 'close': last_candle.close, 'volume': 0}
                # creo la nueva candle, con toda la info, el timeframe y el "exchange"
                new_candle = Candle(candle_info, self.tf, "parse_trade")

                self.candles.append(new_candle)

                # reemplazo la última con la nueva
                last_candle = new_candle

            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            # creo la nueva candle, con toda la info, el timeframe y el "exchange"
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles.append(new_candle)

            return "new_candle"

        # Comenzar un nuevo candle
        # Viceversa que lo anterior. No update, es un nuevo candle
        elif timestamp >= last_candle.timestamp + self.tf_equiv:
            new_ts = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
            # creo la nueva candle, con toda la info, el timeframe y el "exchange"
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles.append(new_candle)

            logger.info("%s New candle for %s %s", self.exchange, self.contract.symbol, self.tf)

            return "new_candle"

    def _check_order_status(self, order_id):

        order_status = self.client.get_order_status(self.contract, order_id)

        if order_status is not None:
            logger.info("%s order status: %s", self.exchange, order_status.status)

            if order_status.status == "filled":
                # loop sobre la lista de trades para identificar a este por el id
                for trade in self.trades:
                    if trade.entry_id == order_id:
                        trade.entry_price = order_status.avg_price
                        break
                return

        # chequeo hasta que el order_status este lleno cada 2 segundos
        t = Timer(2.0, lambda: self._check_order_status(order_id))
        t.start()

    def _open_position(self, signal_result: int):

        trade_size = self.client.get_trade_size(self.contract, self.candles[-1].close, self.balance_pct)
        # Si es None, algo anduvo mal
        if trade_size is None:
            return

        order_side = "buy" if signal_result == 1 else "sell"
        # agregamos la posicion al log
        position_side = "long" if signal_result == 1 else "short"
        self._add_log(f"{position_side.capitalize()} signal on {self.contract.symbol} {self.tf}")

        # pasamos la orden al cliente
        order_status = self.client.place_order(self.contract, "MARKET", trade_size, order_side)

        if order_status is not None:
            # request succesful
            self._add_log(f"{order_side.capitalize()} order placed on {self.exchange} | Status: {order_status.status}")
            # muy importante: cambio el estado a True cuando se hace place de la orden
            self.ongoing_position = True

            avg_fill_price = None

            # Binance y Bitmex devuelven filled cuando la orden está completa, pero otros exchanges pueden devolver
            # otra palabra (executed, etc).
            if order_status.status == "filled":
                # guardo el precio promedio de ejecución de la orden
                avg_fill_price = order_status.avg_price
            else:
                # puede pasar que la orden no se complete de una, sino que demore , entonces voy a ir chequeando
                # cada x tiempo si se completó
                t = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
                t.start()

            # Va a ser una lista que guarde el Trade.
            new_trade = Trade({"time": int(time.time() * 1000), "entry_price": avg_fill_price,
                               "contract": self.contract, "strategy": self.stat_name, "side": position_side,
                               "status": "open", "pnl": 0, "quantity": trade_size, "entry_id": order_status.order_id})

            self.trades.append(new_trade)

    def _check_tp_sl(self, trade: Trade):

        # Variables boolean que disparan el take profit o stop loss
        tp_triggered = False
        sl_triggered = False

        # comparo el precio actual contra el precio de entrada del trade
        price = self.candles[-1].close

        if trade.side == "long":
            if self.stop_loss is not None:
                # si el precio es menor o igual al stop loss exit price
                if price <= trade.entry_price * (1 - self.stop_loss / 100):
                    sl_triggered = True
            if self.take_profit is not None:
                # si el precio es menor o igual al stop loss exit price
                if price >= trade.entry_price * (1 + self.take_profit / 100):
                    tp_triggered = True

        elif trade.side == "short":
            if self.stop_loss is not None:
                # si el precio es menor o igual al stop loss exit price
                if price >= trade.entry_price * (1 + self.stop_loss / 100):
                    sl_triggered = True
            if self.take_profit is not None:
                # si el precio es menor o igual al stop loss exit price
                if price <= trade.entry_price * (1 - self.take_profit / 100):
                    tp_triggered = True

        # Si alguno de los 2 es True mandamos log que informa el exit position
        if tp_triggered or sl_triggered:

            self._add_log(f"{'Stop loss' if sl_triggered else 'Take profit'} for {self.contract.symbol} {self.tf}")
            # Informo la parte contraria SELL si estaba long, BUY si estaba short
            order_side = "SELL" if trade.side == "long" else "BUY"
            order_status = self.client.place_order(self.contract, "MARKET", trade.quantity, order_side)

            if order_status is not None:
                self._add_log(f"Exit order on {self.contract.symbol} {self.tf} placed successfully")
                trade.status = "closed"
                self.ongoing_position = False


class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Technical")

        # Atributos particulares de la clase
        self._ema_fast = other_params['ema_fast']
        self._ema_slow = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']

        self._rsi_length = other_params['rsi_length']

    # el rsi se puede calcular con las ema que figuran como atributos (fast, slow, signal)
    def _rsi(self):
        # lista de precios de cierre de cada día para ir armando las ema
        close_list = []
        for candle in self.candles:
            close_list.append(candle.close)

        # convierto la lista a un Objeto Series de Pandas
        closes = pd.Series(close_list)

        delta = closes.diff().dropna()

        # separo las variaciones positivas de las negativas
        up, down = delta.copy(), delta.copy()
        # si es menor a 0 la seteo en 0, ya que la lista solo registra up
        up[up < 0] = 0
        # si es mayor a 0 la seteo en 0, ya que la lista solo registra down
        down[down > 0] = 0

        # calculo las ema para el rsi - com significa center of mass
        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()
        # convierto los negativos a positivos para registrarlos en la lista con abs()
        avg_loss = down.abs().ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - 100 / (1 + rs)
        rsi = rsi.round(2)

        return rsi.iloc[-2]

    # el macd se puede calcular con las ema que figuran como atributos (fast, slow, signal)
    def _macd(self) -> Tuple[float, float]:

        # lista de precios de cierre de cada día para ir armando las ema
        close_list = []
        for candle in self.candles:
            close_list.append(candle.close)

        # convierto la lista a un Objeto Series de Pandas
        closes = pd.Series(close_list)

        # ewm provee los calculos para exponencial weighted functions. Lo calculo junto a un mean y sale la ema
        # podría usar una librería también, pero por ahora lo hacemos así
        # el span es el periodo elegido en la interface de parameters del GUI para la ema_fast
        ema_fast = closes.ewm(span=self._ema_fast).mean()
        ema_slow = closes.ewm(span=self._ema_slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self._ema_signal).mean()

        # retorno la linea y señal de la candle previa [-2] (ya que [-1] es la última
        return macd_line.iloc[-2], macd_signal.iloc[-2]

    # método para determinar si debemos ir long o short y definir cómo actua la estrategia. Fundamental
    # definir cómo actua la estrategia acá, en check_signal()
    def _check_signal(self):
        # llamo al método self._macd() que devuelve 2 valores : line y signal
        macd_line, macd_signal = self._macd()

        # llamo al método self._rsi() que devuelve 1 valor
        rsi = self._rsi()

        if rsi < 30 and macd_line > macd_signal:
            return 1
        elif rsi > 70 and macd_line < macd_signal:
            return -1
        else:
            return 0

    # En technical, sólo chequeamos el trade cuando hay un nuevo candle
    def check_trade(self, tick_type: str):

        # Si viene un nuevo candle y ongoing_position es False (es decir que no hay nada ya abierto)
        if tick_type == "new_candle" and not self.ongoing_position:
            signal_result = self._check_signal()

            # -1 se refiere a short y 1 a long, es decir si el signal_result ya dio para hacer un short o long
            if signal_result in [1, -1]:
                # abro la posición
                self._open_position(signal_result)


class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, timeframe: str, balance_pct: float,
                 take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(client, contract, exchange, timeframe, balance_pct, take_profit, stop_loss, "Breakout")

        # Atributos particulares de la clase
        self.min_volume = other_params['min_volume']

    # método para determinar si debemos ir long o short y definir cómo actua la estrategia. Fundamental
    # definir cómo actua la estrategia acá, en check_signal()
    def _check_signal(self) -> int:
        # return un int ya que si es long será 1 , short -1 , nada 0

        # long
        if self.candles[-1].close > self.candles[-2].high and self.candles[-1].volume > self.min_volume:
            return 1
        # short
        elif self.candles[-1].close < self.candles[-2].low and self.candles[-1].volume > self.min_volume:
            return -1
        else:
            return 0

    def check_trade(self, tick_type: str):

        # no hay, como en Technical, una restricción de un new_candle, sólo ongoing_position debe ser False
        if not self.ongoing_position:
            signal_result = self._check_signal()

            # -1 se refiere a short y 1 a long, es decir si el signal_result ya dio para hacer un short o long
            if signal_result in [1, -1]:
                # abro la posición
                self._open_position(signal_result)
