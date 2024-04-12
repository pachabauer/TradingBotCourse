import tkinter as tk
import logging
from connectors.binance_futures import BinanceFuturesClient

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

    binance = BinanceFuturesClient(True)
    print(binance.get_historical_candles('BTCUSDT', "1h"))

    root = tk.Tk()

    # mainloop() hace que la ventana no se cierre automaticamente,
    # sino que se queda esperando hasta que el usuario realice una accion.
    root.mainloop()