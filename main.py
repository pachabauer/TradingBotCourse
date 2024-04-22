import tkinter as tk
import logging
from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmex_futures import BitmexClient

logger = logging.getLogger()

#se setea el mínimo nivel de logging --> INFO indica que solo info, warning and error serán mostrados
logger.setLevel(logging.INFO)

# lo usamos para enviar el mensaje de logging para que se vea en la consola
stream_handler = logging.StreamHandler()

# le asigno el formato al mensaje de logging, en este caso fecha hora, level (info, warning, etc) y mensaje
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# Establecemos un fileHandler para guardar el archivo del log. Con stream_handler no puedo hacerlo
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
# logging.DEBUG lo usamos (en vez de INFO) para que guarde un mayor nivel de detalle
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# logger.debug("This message is important only when debugging this program")
# logger.info("This message just shows basic information")
# logger.warning("This message is about something you should pay attention to")
# logger.error("This message helps to debug an error that occurred in your program")

if __name__== '__main__':

    # instanciamos la clase BinanceFuturesClient y le pasamos las keys y el True para referirse a testnet
    # binance = BinanceFuturesClient("15cafcccb0b80222a789be92c7d19314efea7cdf6cf275438d0ba519babbdbb1",
    #                                "95027f038a128c189761aef63abbb5ef8bb8654c64d004b0e85443b44866530c",
    #                                True)

    # contracts = binance.get_contracts()
    # for symbol, contract in contracts.items():
    #     print(f"Símbolo: {symbol}")
    #     print(f"Base Asset: {contract.base_asset}")
    #     print(f"Quote Asset: {contract.quote_asset}")
    #     print(f"Precisión del Precio: {contract.price_decimals}")
    #     print(f"Precisión de la Cantidad: {contract.quantity_decimals}")
    #     print()

    bitmex = BitmexClient('IrMjnDtKOJPa4vKQdY8eEFmK', 'RmxMg044vAPb2Kr8uF1YUbUzElba_yVoG3XKolFuXv2kcPGW', True)



    print(bitmex.contracts['XBTUSD'].base_asset, bitmex.contracts['XBTUSD'].price_decimals)
    print(bitmex.balances['XBt'].wallet_balance)

    #contracts = bitmex.get_contracts()

    root = tk.Tk()

    # mainloop() hace que la ventana no se cierre automaticamente,
    # sino que se queda esperando hasta que el usuario realice una accion.
    root.mainloop()