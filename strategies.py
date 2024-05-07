import logging

from typing import *
from models import *

logger = logging.getLogger()

# Creo la variable global TF_EQUIV (timeframe equivalent) para representar los tf en milisegundos
TF_EQUIV = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}

# Clase base de cualquier estrategia que tenga el TradingBot
class Strategy():
    def __init__(self, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float,
                 stop_loss: float):

        # Atributos comunes a cualquier estrategia del TradingBot
        self.contract = contract
        self.exchange = exchange
        self.tf = timeframe
        self.tf_equiv = TF_EQUIV[timeframe] * 1000 # convierto a milisegundos
        self.balance_pct = balance_pct
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        # Cada vez que creo una estrategia traigo las candles del contrato que voy a operar
        self.candles: List[Candle] = []

    # creo un método para parsear la información del trade (precio, quantity, stop, etc)
    def parse_trades(self, price: float, size: float, timestamp: int) -> str:
        last_candle = self.candles[-1]

        # A su vez este método tendrá 3 posibilidades:

        # Hacer update de nuevos valores de un candle
        # definamos que estamos en un timeframe de 30m, es decir 1800 segundos
        # esto sería si el timestamp de la candle es 1020, quiere decir que estamos en el candle, ya que va
        # de 0 a 1800 (30m en segundos) + los milisegundos y sigue en la misma candle, haremos el update
        if timestamp < last_candle.timestamp + self.tf_equiv:

            last_candle.close = price
            last_candle.volume = size
            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price

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
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume':size}
            # creo la nueva candle, con toda la info, el timeframe y el "exchange"
            new_candle = Candle(candle_info, self.tf, "parse_trade")

            self.candles.append(new_candle)

            logger.info("%s New candle for %s %s", self.exchange, self.contract.symbol, self.tf)

            return "new_candle"


class TechnicalStrategy(Strategy):
    def __init__(self, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(contract, exchange, timeframe, balance_pct, take_profit, stop_loss)

        # Atributos particulares de la clase
        self._ema_fast = other_params['ema_fast']
        self._ema_slow = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']


class BreakoutStrategy(Strategy):
    def __init__(self, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(contract, exchange, timeframe, balance_pct, take_profit, stop_loss)

        # Atributos particulares de la clase
        self.min_volume = other_params['min_volume']





