import logging
import time
import requests
import hmac
import hashlib
import websocket
import json
import typing
import dateutil.parser
import threading
from models import *
from urllib.parse import urlencode

from strategies import TechnicalStrategy, BreakoutStrategy

logger = logging.getLogger()


# El init es igual al de Binance (salvo por los url y demás)
class BitmexClient:

    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.bitmex.com"
            self._wss_url = "wss://testnet.bitmex.com/realtime"
        else:
            self._base_url = "https://www.bitmex.com"
            self._wss_url = "wss://www.bitmex.com/realtime"

        self._public_key = public_key
        self._secret_key = secret_key

        self._ws = None

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()
        self.prices = dict()

        # Agrego variable para almacenar las candles de cada estrategia que inicie
        # el Union significa que puede adoptar un valor u otro "Technical o Breakout"
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        # agrego una lista de logs, que son los que se van a ir mostrando en la interface visual al usuario
        self.logs = []



        # Hay 3 diferencias entre el WS de Bitmex y Binance:
        #   1- La URL
        #   2- La data que recibimos en el on_message() está estructurada diferente
        #   3- La forma que nos suscribimos al feed (channel en Binance). Trae la información para todos los
        #       contratos, en vez de para uno en particular.

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Bitmex Client succesfully initialized")

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log":msg, "displayed":False})

    # Acá cambian la cantidad de parámetros para el signature, ya que así lo especifica la documentación de Bitmex.
    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:

        # Si no especificamos la data que queremos (toda por defecto) no hace falta pasar el ? y el urlencode(data)
        # Si no hacemos este if y la data va vacia, dará error
        if len(data) > 0:
            message = method + endpoint + "?" + urlencode(data) + expires
        else:
            message = method + endpoint + expires

        return hmac.new(self._secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _make_request(self, method: str, endpoint: str, data: typing.Dict):

        headers = dict()
        expires = str(int(time.time()) + 5)
        headers['api-expires'] = expires
        headers['api-key'] = self._public_key
        headers['api-signature'] = self._generate_signature(method, endpoint, expires, data)

        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None

        else:
            raise ValueError()

        if response.status_code == 200:
            return response.json()

        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self) -> typing.Dict[str, Contract]:
        instruments = self._make_request("GET", "/api/v1/instrument/active", dict())

        contracts = dict()

        if instruments is not None:
            for instrument_data in instruments:
                # estructura de diccionario (key,data), siendo el pair la key y la data es toda la lista
                contracts[instrument_data['symbol']] = Contract(instrument_data, "bitmex")

        return contracts

    def get_balances(self) -> typing.Dict[str, Balance]:
        # genero los datos para identificarse, para pasarle al make_request().
        data = dict()
        data['currency'] = "all"

        margin_data = self._make_request("GET", "/api/v1/user/margin", data)
        balances = dict()

        if margin_data is not None:
            for a in margin_data:
                balances[a['currency']] = Balance(a, "bitmex")

        return balances

    def get_historical_candles(self, contract: Contract, timeframe: str) -> typing.List[Candle]:
        data = dict()

        data['symbol'] = contract.symbol
        # partial se refiere a que si una candle aun no está completada (por ejemplo candles de 1h y son las
        # 20.30, va a traer la candle de las 20 con la última información hasta el momento (20.30), en vez de no
        # traerla (si pongo False))
        data['partial'] = True
        data['binSize'] = timeframe
        # número máximo permitido por Bitmex para traer Candles en un request
        data['count'] = 500
        data['reverse'] = True

        raw_candles = self._make_request("GET", "/api/v1/trade/bucketed", data)
        candles = []

        if raw_candles is not None:
            for candle in reversed(raw_candles):
                candles.append(Candle(candle, timeframe, "bitmex"))

        return candles

    def place_order(self, contract: Contract, order_type: str, quantity: int, side: str, price=None,
                    tif=None) -> OrderStatus:
        data = dict()

        data['symbol'] = contract.symbol
        data['side'] = side.capitalize()
        data['orderQty'] = round(quantity / contract.lot_size) * contract.lot_size
        data['orderType'] = order_type.capitalize()

        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size,8)

        if tif is not None:
            data['timeInForce'] = tif

        order_status = self._make_request('POST', '/api/v1/order', data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "bitmex")

        return order_status

    def cancel_order(self, order_id: str) -> OrderStatus:
        data = dict()

        data['orderID'] = order_id

        order_status = self._make_request('DELETE', '/api/v1/order', data)

        if order_status is not None:
            # trae una lista de diccionarios el DELETE, ya que podemos cancelar mas de 1 orden con un request.
            # por eso el order_status[0] se refiere al primer diccionario
            order_status = OrderStatus(order_status[0], "bitmex")

        return order_status

    # Este método, a diferencia de Binance, no trae al principio el order_id directamente, sino que trae una lista de
    # diccionarios. En esa lista debemos buscar nuestro order_id (de nuestra orden pasada previamente) y una vez
    # encontrado, devolverá el estado.
    def get_order_status(self, order_id: str, contract: Contract) -> OrderStatus:

        data = dict()
        data['symbol'] = contract.symbol
        # el reverse = True, significa que de toda la lista de id's que encuentre, traerá los más actuales (nuevos)
        # primero.
        data['reverse'] = True

        order_status = self._make_request('GET', '/api/v1/order', data)

        if order_status is not None:
            for order in order_status:
                if order['orderID'] == order_id:
                    return OrderStatus(order, "bitmex")

    # Websocket Methods

    def _start_ws(self):

        # lleva como argumentos: url y callback functions
        self._ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
                                          on_error=self._on_error, on_message=self._on_message)

        # inicia el loop infinito esperando mensajes del websocket server
        # Si llega a dar error o se cae la conexión, espera 2 segundos para reconectarse automaticamente
        while True:
            try:
                self._ws.run_forever()
            except Exception as e:
                logger.error("Bitmex error in run_forever() method: %s", e)
            time.sleep(2)

    def _on_open(self, ws):
        logger.info("Bitmex Websocket connection opened")
        # Acá se suscribe al channel instrument
        self.subscribe_channel('instrument')

        # Acá se suscribe al channel trade para sacar datos de las velas del websocket
        self.subscribe_channel("trade")

    def _on_close(self, ws):
        logger.warning("Bitmex Websocket connection closed")

    def _on_error(self, ws, msg: str):
        logger.error("Bitmex Websocket connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        # Una vez recibidos los datos del ws, convierto el jsonString a jsonObject, a fin de mostrarlo claramente
        data = json.loads(msg)

        # la e se refiere al evento (al canal) del cual estoy recibiendo la información
        if "table" in data:
            if data['table'] == "instrument":

                for d in data['data']:
                    symbol = d['symbol']
                    if symbol not in self.prices:
                        self.prices[symbol] = {'bid': None, 'ask': None}

                    if 'bidPrice' in d:
                        self.prices[symbol]['bid'] = d['bidPrice']
                    if 'askPrice' in d:
                        self.prices[symbol]['ask'] = d['askPrice']

            if data['table'] == "trade":

                for d in data['data']:

                    symbol = d['symbol']
                    # convierto de ISO 8601 a timestamp y como queda en milisegundos multiplico por 1000 para pasar
                    # a segundos  y luego lo paso a int
                    ts = int(dateutil.parser.isoparse(d['timestamp']).timestamp() * 1000)

                    # Hago loop en la estrategia cada vez que recibo nueva información de precios de candles
                    # para ir viendo como afecta el nuevo precio a la estrategia (TP, SL , etc)
                    for key, strat in self.strategies.items():
                        if strat.contract.symbol == symbol:
                            # paso para parsear el trade: precio (p), quantity (q) y timestamp (T)
                            strat.parse_trades(float(d['price']), float(d['size']), ts)


    def subscribe_channel(self, topic: str):
        data = dict()
        data['op'] = "subscribe"
        data['args'] = []
        data['args'].append(topic)

        # La función json.dumps() convertirá un subconjunto de objetos de Python en una cadena json.
        # No todos los objetos son convertibles
        # es posible que necesites crear un diccionario de datos antes de serializarlos a JSON
        # Hago esto ya que necesito pasarle un JSON String al self.ws.send()
        try:
            self._ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %s", topic, e)
