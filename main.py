import tkinter as tk
import logging
from bitmex_futures import get_instruments

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

    bitmex_instruments = get_instruments()

    root = tk.Tk()

    # de entrada defino el background color de la pantalla.
    root.configure(bg="gray12")

    i = 0
    j = 0

    # defino una tupla para el tipo de letra que van a llevar los widget
    calibri_font = ("Calibri", 11, "normal")

    # ahora vamos a crear los labels para que se vean en el widget (interface)
    for instrument in bitmex_instruments:

        # el método Label() necesita argumentos --> en donde va a ir del window (en este caso root, pero puede haber
        # otras ventanas, el texto que va a mostrar ese label)
        # también tiene la posibilidad de incorporar bordes y el relief es el tipo de borde
        # bg es el background color y fg es el color y tipo de la font
        label_widget = tk.Label(root, text= instrument, bg='gray12', fg='SteelBlue1', font= calibri_font, borderwidth=1, relief=tk.SOLID, width=13)

        # también debo especificar (sino no se ven los labels) la forma de visualización: se pueden usar 2 métodos:
        # pack() --> que hace que se vea cada label en una ventana separada abajo de otra. Será útil cuando hagamos
        #            los 4 subframes de la interface, una con cada ventana.
        # grid() --> que hace que se vea como filas. Este es el más indicado cuando queremos mostrar listas de datos.
        # sticky es la forma de hacer que las columnas ocupen todo el espacio a la izquierda y derecha, a fin que
        # queden uniformes.
        label_widget.grid(row = i, column = j, sticky='ew')

        if i == 4:
            j +=1
            i = 0
        else:
            i += 1

    # mainloop() hace que la ventana no se cierre automaticamente,
    # sino que se queda esperando hasta que el usuario realice una accion.
    root.mainloop()