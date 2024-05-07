import logging
import pandas as pd
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
        self.tf_equiv = TF_EQUIV[timeframe] * 1000  # convierto a milisegundos
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
            last_candle.volume += size
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
            candle_info = {'ts': new_ts, 'open': price, 'high': price, 'low': price, 'close': price, 'volume': size}
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
        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods = self._rsi_length).mean()
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
        print(closes)

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

        print(rsi, macd_line, macd_signal)

        if rsi < 30 and macd_line > macd_signal:
            return 1
        elif rsi > 70 and macd_line < macd_signal:
            return -1
        else:
            return 0


class BreakoutStrategy(Strategy):
    def __init__(self, contract: Contract, exchange: str, timeframe: str, balance_pct: float, take_profit: float,
                 stop_loss: float, other_params: Dict):
        super().__init__(contract, exchange, timeframe, balance_pct, take_profit, stop_loss)

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
