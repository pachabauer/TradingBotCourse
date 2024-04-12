import logging
import requests

logger = logging.getLogger()

"https://www.bitmex.com/api/v1"

def get_instruments():

    response_object = requests.get("https://www.bitmex.com/api/v1/instrument/active")
    instruments = []

    for contract in response_object.json():
        instruments.append(contract['symbol'])

    return instruments

print(get_instruments())



