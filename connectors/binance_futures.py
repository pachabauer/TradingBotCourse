import logging
import time

import requests

# libreria para hacer más fácil y clara la lectura de los print()
import pprint

# librerías para generar los hashcodes
import hmac
import hashlib

from urllib.parse import urlencode

import websocket

# permite la ejecución de varios threads en simultaneo. Esto permite ejecutar, por ejemplo,
# un loop infinito en un thread mientras que el programa hace otras tareas en otro thread.
# De esa manera, puedo establecer una conexión websocket "infinita" (para obtener datos en real time
# y seguir ejecutando: órdenes, etc.
import threading

import json

from models import *
import typing

logger = logging.getLogger()

# hacemos una clase que contendrá varios métodos relacionados
class BinanceFuturesClient:

    # el constructor es __init__
    # testnet es un boolean que se usa de entrada (en este caso) para identificar si trabajamos
    # sobre test o sobre real (true or false)
    # Incorporamos los datos de public_key y secret_key y los instanciamos en la clase main
    # el : a un argumento permite especificar el tipo de dato, para hacerlo tipado
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = "wss://fstream.binance.com/ws"


        self._public_key = public_key
        self._secret_key = secret_key

        # Este header se pide como requisito en los docs de Binance para pasar el APIKEY
        self._headers = {'X-MBX-APIKEY': self._public_key}

        self.contracts = self.get_contracts()
        self.balances = self.get_balances()

        self.prices = dict()

        self.logs = []

        self._ws_id = 1
        self._ws = None

        t = threading.Thread(target=self._start_ws)
        t.start()

        logger.info("Binance Futures Client succesfully initialized")

    def _add_log(self, msg: str):
        logger.info("%s", msg)
        self.logs.append({"log":msg, "displayed":False})

    # typing es una librería que nos permite asignar un dato como Objeto. Como Integer en java (en vez de int)
    # el _ delante del método, lo indica como privado de la clase. No lo puedo usar de cualquier instancia
    def _generate_signature(self, data: typing.Dict) -> str:
        # hmac lleva 3 parámetros: la secret_key, un message (queryString) y el tipo SHA256
        # encode() sirve para convertir el string a byte
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    # method se refiere a los de Http (GET, POST, etc) y el endpoint apunta a la url que usaremos (ver bien test o real)
    def _make_request(self, method: str, endpoint: str, data: typing.Dict):
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "POST":
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        elif method == "DELETE":
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error("Connection error while making %s request to %s: %s", method, endpoint, e)
                return None
        else:
            raise ValueError()

        if response.status_code == 200:
            return  response.json()
        else:
            # los %s son variables method y endpoint, response (los 2)
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    # --> refiere al tipo que va a devolver el método
    def get_contracts(self) -> typing.Dict[str, Contract]:
        exchange_info = self._make_request("GET", "/fapi/v1/exchangeInfo", dict())

        contracts = dict()

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                # estructura de diccionario (key,data), siendo el pair la key y la data es toda la lista
                contracts[contract_data['symbol']] = Contract(contract_data, "binance")

        return contracts

    # para definir el tipo de dato de contract, especifico su model (su clase).
    # a su vez, puedo especificar el tipo de dato que devuelve el método con -> y el typing correspondiente
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c, interval, "binance"))

        return candles

    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, float]:
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self._make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            # si el contract.symbol no está en prices (al principio nunca estará), lo agrega.
            # si ya está, lo actualiza.
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]

    def get_balances(self) -> typing.Dict[str, Balance]:
        # genero los datos para identificarse, para pasarle al make_request(). El timestamp lo saca de la hora local
        # de la pc, la cual debe estar sincronizada con el huso horario local, ya que sino podría fallar con
        # el time definido por Binance (en este caso) en su servidor.
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        balances = dict()
        account_data = self._make_request("GET", "/fapi/v2/account", data)

        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = Balance(a, "binance")

        return balances

    def place_order(self, contract: Contract, side: str, quantity: float, order_type: str,
                    price=None, tif=None) -> OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side
        data['quantity'] = round(round(quantity / contract.lot_size) * contract.lot_size, 8)
        data['type'] = order_type

        # Son los argumentos no mandatorios, es decir no obligatorios
        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size,8)
        if tif is not None:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("POST", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "binance")

        return order_status

    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['orderId'] = order_id

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("DELETE", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "binance")

        return order_status

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request("GET", "/fapi/v1/order", data)

        if order_status is not None:
            order_status = OrderStatus(order_status, "binance")

        return order_status

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
                logger.error("Binance error in run_forever() method: %s", e)
            time.sleep(2)

    def _on_open(self,ws):
        logger.info("Binance Websocket connection opened")
        # Acá se suscribe al channel bookTicker
        self.subscribe_channel(list(self.contracts.values()), "bookTicker")

    def _on_close(self,ws):
        logger.warning("Binance Websocket connection closed")

    def _on_error(self, ws, msg: str):
        logger.error("Binance Websocket connection error: %s", msg)

    def _on_message(self, ws, msg: str):

        # Una vez recibidos los datos del ws, convierto el jsonString a jsonObject, a fin de mostrarlo claramente
        data = json.loads(msg)

        # la e se refiere al evento (al canal) del cual estoy recibiendo la información
        if "e" in data:
            if data['e'] == "bookTicker":

                symbol = data['s']
                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])


    # Para obtener data, necesito suscribirme a "canales". Esto es, una especie de endpoint, que envía datos
    # los cuales son recibidos por el ws y transmitidos al programa
    # https://binance-docs.github.io/apidocs/testnet/en/#live-subscribing-unsubscribing-to-streams
    def subscribe_channel(self, contracts:typing.List[Contract], channel: str):
        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        for contract in contracts:
        # ver documentación : ticker en minusculas mas el @ y el bookTicker
            data['params'].append(contract.symbol.lower() + "@" + channel)
        data['id'] = self._ws_id

        # La función json.dumps() convertirá un subconjunto de objetos de Python en una cadena json.
        # No todos los objetos son convertibles
        # es posible que necesites crear un diccionario de datos antes de serializarlos a JSON
        # Hago esto ya que necesito pasarle un JSON String al self.ws.send()
        try:
            self._ws.send(json.dumps(data))
        except Exception as e:
            logger.error("Websocket error while subscribing to %s %s updates: %s", len(contracts), channel, e)

        self._ws_id += 1