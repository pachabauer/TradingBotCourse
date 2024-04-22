import logging
import time
import requests
import hmac
import hashlib
import websocket
import json
import typing
import pprint
import threading
from models import *
from urllib.parse import urlencode


logger = logging.getLogger()

# El init es igual al de Binance (salvo por los url y demás)
class BitmexClient:

    def __init__(self, public_key:str, secret_key:str, testnet:bool):
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

        # t = threading.Thread(target=self._start_ws)
        # t.start()

        logger.info("Bitmex Client succesfully initialized")

    # Acá cambian la cantidad de parámetros para el signature, ya que así lo especifica la documentación de Bitmex.
    def _generate_signature(self, method: str, endpoint: str, expires: str, data: typing.Dict) -> str:

        # Si no especificamos la data que queremos (toda por defecto) no hace falta pasar el ? y el urlencode(data)
        # Si no hacemos este if y la data va vacia, dará error
        if len(data) > 0:
            message = method + endpoint + "?" + urlencode(data) + expires
        else:
            message = method + endpoint + expires

        return hmac.new(self._secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()



    def _make_request(self, method:str, endpoint:str, data: typing.Dict):

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

        else :
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





