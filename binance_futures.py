import logging
import requests
#libreria para hacer más fácil y clara la lectura de los print()
import pprint

logger = logging.getLogger()

"https://fapi.binance.com"

def get_contracts():

    response_object = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")

    contracts = []
    for contract in response_object.json()['symbols']:
        contracts.append(contract['pair'])

    return contracts

print(get_contracts())
