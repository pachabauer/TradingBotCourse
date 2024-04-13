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

logger = logging.getLogger()

# hacemos una clase que contendrá varios métodos relacionados
class BinanceFuturesClient:

    # el constructor es __init__
    # testnet es un boolean que se usa de entrada (en este caso) para identificar si trabajamos
    # sobre test o sobre real (true or false)
    # Incorporamos los datos de public_key y secret_key y los instanciamos en la clase main
    def __init__(self, public_key, secret_key, testnet):
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
            self.wss_url = "wss://stream.binancefuture.com/ws"
        else:
            self.base_url = "https://fapi.binance.com"
            self.wss_url = "wss://fstream.binance.com/ws"


        self.public_key = public_key
        self.secret_key = secret_key

        # Este header se pide como requisito en los docs de Binance para pasar el APIKEY
        self.headers = {'X-MBX-APIKEY': self.public_key}

        self.prices = dict()

        self.id = 1
        self.ws = None

        t = threading.Thread(target=self.start_ws)
        t.start()

        logger.info("Binance Futures Client succesfully initialized")

    def generate_signature(self, data):
        # hmac lleva 3 parámetros: la secret_key, un message (queryString) y el tipo SHA256
        # encode() sirve para convertir el string a byte
        return hmac.new(self.secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    # method se refiere a los de Http (GET, POST, etc) y el endpoint apunta a la url que usaremos (test o real)
    def make_request(self, method, endpoint, data):
        if method == "GET":
            response = requests.get(self.base_url + endpoint, params=data, headers=self.headers)
        elif method == "POST":
            response = requests.post(self.base_url + endpoint, params=data, headers=self.headers)
        elif method == "DELETE":
            response = requests.delete(self.base_url + endpoint, params=data, headers=self.headers)
        else:
            raise ValueError()

        if response.status_code == 200:
            return  response.json()
        else:
            # los %s son variables method y endpoint, response (los 2)
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    def get_contracts(self):
        # como parámetro data del método make_request no hace falta poner nada (ver docs Binance) , por eso va None
        exchange_info = self.make_request("GET", "/fapi/v1/exchangeInfo", None)

        contracts = dict()

        if exchange_info is not None:
            for contract_data in exchange_info['symbols']:
                # estructura de diccionario (key,data), siendo el pair la key y la data es toda la lista
                contracts[contract_data['pair']] = contract_data

        return contracts

    def get_historical_candles(self, symbol, interval):
        data = dict()
        data['symbol'] = symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self.make_request("GET", "/fapi/v1/klines", data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append([c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])])

        return candles

    def get_bid_ask(self, symbol):
        data = dict()
        data['symbol'] = symbol
        ob_data = self.make_request("GET", "/fapi/v1/ticker/bookTicker", data)

        if ob_data is not None:
            if symbol not in self.prices:
                self.prices[symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[symbol]['ask'] = float(ob_data['askPrice'])

        return self.prices[symbol]

    def get_balances(self):
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        balances = dict()
        account_data = self.make_request("GET", "/fapi/v2/account", data)

        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = a

        return balances

    def place_order(self, symbol, side, quantity, order_type, price=None, tif=None):
        data = dict()
        data['symbol'] = symbol
        data['side'] = side
        data['quantity'] = quantity
        data['type'] = order_type

        # Son los argumentos no mandatorios, es decir no obligatorios
        if price is not None:
            data['price'] = price
        if tif is not None:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("POST", "/fapi/v1/order", data)

        return order_status

    def cancel_order(self, symbol, order_id):
        data = dict()
        data['symbol'] = symbol
        data['orderId'] = order_id

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("DELETE", "/fapi/v1/order", data)

        return order_status

    def get_order_status(self, symbol, order_id):
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = symbol
        data['orderId'] = order_id
        data['signature'] = self.generate_signature(data)

        order_status = self.make_request("GET", "/fapi/v1/order", data)

        return order_status

    def start_ws(self):

        # lleva como argumentos: url y callback functions
        self.ws = websocket.WebSocketApp(self.wss_url, on_open=self.on_open, on_close=self.on_close,
                                    on_error=self.on_error, on_message=self.on_message)

        # inicia el loop infinito esperando mensajes del websocket server
        self.ws.run_forever()

    def on_open(self,ws):
        logger.info("Binance Websocket connection opened")
        self.subscribe_channel("BTCUSDT")

    def on_close(self,ws):
        logger.warning("Binance Websocket connection closed")

    def on_error(self, ws, msg):
        logger.error("Binance Websocket connection error: %s", msg)

    def on_message(self, ws, msg):

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

                print(self.prices[symbol])



    # Para obtener data, necesito suscribirme a "canales". Esto es, una especie de endpoint, que envía datos
    # los cuales son recibidos por el ws y transmitidos al programa
    # https://binance-docs.github.io/apidocs/testnet/en/#live-subscribing-unsubscribing-to-streams
    def subscribe_channel(self, symbol):
        data = dict()
        data['method'] = "SUBSCRIBE"
        data['params'] = []

        # ver documentación : ticker en minusculas mas el @ y el bookTicker
        data['params'].append(symbol.lower() + "@bookTicker")
        data['id'] = self.id

        # La función json.dumps() convertirá un subconjunto de objetos de Python en una cadena json.
        # No todos los objetos son convertibles
        # es posible que necesites crear un diccionario de datos antes de serializarlos a JSON
        # Hago esto ya que necesito pasarle un JSON String al self.ws.send()
        self.ws.send(json.dumps(data))

        self.id += 1