## Este módulo es para armar la interface de estrategias, no para crear estrategias en sí .

import tkinter as tk
import typing
from interface.styling import *
from connectors.binance_futures import BinanceFuturesClient
from connectors.bitmex_futures import BitmexClient

class StrategyEditor(tk.Frame):
    # paso una lista de contratos de cada exchange, para que cuando los seleccione en el box, aparezca un listado
    # de ellos y no sea posible agregar o escribir cualquier cosa.
    # agrego 2 parámetros  binance y bitmex, ya que para cambiar de estrategia en el switch_strategy()
    # necesitaré acceder a los conectores debido a que voy a detener la conexión a un exchange y conectarme al otro
    # y viceversa.

    def __init__(self, root, binance: BinanceFuturesClient, bitmex: BitmexClient, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Creo la variable de instancia que pasé como argumento, ya que así podré acceder al método add_log() del
        # root_component para mostrar un mensaje de log en la interface si el switch_strategy() devuelve return
        # debido a que no se ingresaron la totalidad de los parámetros.
        self.root = root

        # Accedo a los conectores para el método switch_strategy()
        self._exchanges = {"Binance": binance, "Bitmex": bitmex}

        self._all_contracts = []
        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

        # para popular el contract_list de _all_contracts[]
        for exchange, client in self._exchanges.items():
            # para iterar por cada contrato que aparezca del client
            for symbol, contract in client.contracts.items():
                self._all_contracts.append(symbol + "_" + exchange.capitalize())



        # Se crean dos marcos (Frame) para los controles de la interfaz y la tabla de visualización.
        self._commands_frame = tk.Frame(self, bg=BG_COLOR)
        self._commands_frame.pack(side=tk.TOP)
        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._add_button = tk.Button(self._commands_frame, text="Add strategy", font=GLOBAL_FONT,
                                     command=self._add_strategy_row, bg=BG_COLOR2, fg=FG_COLOR)

        self._add_button.pack(side=tk.TOP)

        # Se crean diccionarios para almacenar widgets y una lista de encabezados.
        self.body_widgets = dict()
        self._headers = ["Strategy", "Contract", "Timeframe", "Balance %", "TP %", "SL %"]

        # cada vez que agregue una nueva estrategia (una nueva fila) guardare los valores de los parametros
        # en este diccionario
        self._additional_parameters = dict()

        self._extra_input = dict()

        # Son los widgets que iré completando a lo largo del frame en forma dinámica pertenecientes a los headers.
        # Cómo no son todos los widgets iguales (botones, etiquetas, etc) voy a crear un diccionario que describe
        # a los widgets que iré agregando y los meto todos en una lista
        self._base_params = [
            # las keys son el nombre de la estrategia, un desplegable para elegir el widget a usar
            # el tipo de dato y la estrategia a utilizar (que crearemos mas adelante, llamada Technical o Breakout)
            {"code_name": "strategy_type", "widget": tk.OptionMenu, "data_type": str,
             "values": ["Technical", "Breakout"], "width": 10},
            {"code_name": "contract", "widget": tk.OptionMenu, "data_type": str,
             "values": self._all_contracts, "width": 15},
            {"code_name": "timeframe", "widget": tk.OptionMenu, "data_type": str,
             "values": self._all_timeframes, "width": 7},
            {"code_name": "balance_pct", "widget": tk.Entry, "data_type": float,
             "width": 7},
            {"code_name": "take_profit", "widget": tk.Entry, "data_type": float,
             "width": 7},
            {"code_name": "stop_loss", "widget": tk.Entry, "data_type": float,
             "width": 7},
            # Botones
            {"code_name": "parameters", "widget": tk.Button, "data_type": float,
             "text": "Parameters", "bg": BG_COLOR2, "command": self._show_popup},
            {"code_name": "activation", "widget": tk.Button, "data_type": float,
             "text": "OFF", "bg": "darkred", "command": self._switch_strategy},
            {"code_name": "delete", "widget": tk.Button, "data_type": float,
             "text": "X", "bg": "darkred", "command": self._delete_row},

        ]

        self._extra_params = {

            # Acá queda pendiente de resolver qué pasa si queremos agregar más de un indicador en technical o
            # breakout, ya que en el curso solo muestran uno de cada uno, entonces no agrupan el indicador
            # con sus parámetros, sino que los mandan directo dentro de la lista.
            "Technical": [
                {"code_name": "ema_fast", "name": "MACD Fast Lenght", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_slow", "name": "MACD Slow Lenght", "widget": tk.Entry, "data_type": int},
                {"code_name": "ema_signal", "name": "MACD Signal Lenght", "widget": tk.Entry, "data_type": int}
            ],
            "Breakout": [
                {"code_name": "min_volume", "name": "Minimum Volume", "widget": tk.Entry, "data_type": float}
            ],
        }

        # la función enumerate nos permite acceder al mismo tiempo al valor del elemento de la lista (h)
        # y a la posición (idx)
        # La idea del for es popular los datos de las widgets dinámicamente
        # Se crean etiquetas de encabezado y se colocan en la primera fila de la tabla.
        for idx, h in enumerate(self._headers):
            # uso el inline if para decir si tiene datos, mostrá el remove, sino ""
            header = tk.Label(self._table_frame, text=h, bg=BG_COLOR, fg=FG_COLOR,font=BOLD_FONT)
            header.grid(row=0, column=idx)

        # itero para completar dinámicamente las etiquetas del widget
        # Se inicializan los diccionarios para almacenar widgets y variables.
        for h in self._base_params:
            self.body_widgets[h['code_name']] = dict()
            if h['code_name'] in ["strategy_type", "contract", "timeframe"]:
                self.body_widgets[h['code_name'] + "_var"] = dict()


        # una variable int que se posiciona en la última fila de la tabla y se irá incrementando a medida
        # que se agregue filas (datos) de ["symbol", "exchange", "bid", "ask"]
        # empieza en 1 porque la fila 0 son los headers mencionados
        self._body_index = 1

    # El loop que crea un entry buttom o un menú de opción de widget
    def _add_strategy_row(self):
        b_index = self._body_index

        for col, base_param in enumerate(self._base_params):
            code_name = base_param['code_name']
            if base_param['widget'] == tk.OptionMenu:
                self.body_widgets[code_name + "_var"][b_index] = tk.StringVar()
                # Seteo el primer elemento de la lista como default para la selección de estrategia
                # en este caso cada estrategia tendrá como default BTCUSDT (en el caso de Binance).
                self.body_widgets[code_name + "_var"][b_index].set(base_param['values'][0])
                # Se usa el * delante de una lista para hacer unpack de la misma
                self.body_widgets[code_name][b_index] = tk.OptionMenu(self._table_frame,
                                                                      self.body_widgets[code_name + "_var"][b_index],
                                                                      *base_param['values'])
                self.body_widgets[code_name][b_index].config(width= base_param['width'])

            elif base_param['widget'] == tk.Entry:
                self.body_widgets[code_name][b_index] = tk.Entry(self._table_frame, justify=tk.CENTER)
            elif base_param['widget'] == tk.Button:
                # la parte del command es un quilombo, así que lo explico: el command es lo que dispara el botón
                # al hacer click. En este caso dispara un callback, mediante el lambda method. Pero "guardamos"
                # ese valor disparado por el callback en una variable frozen para que no cambie cada vez
                # que iteramos sobre ese método y quede fijada.
                self.body_widgets[code_name][b_index] = tk.Button(self._table_frame, text=base_param['text'],
                                                                  bg=base_param['bg'], fg= FG_COLOR,
                                                                  command=lambda frozen_command =
                                                                                 base_param['command']:
                                                                                 frozen_command(b_index))
            else:
                continue

            self.body_widgets[code_name][b_index].grid(row=b_index, column= col)

        # Lo uso para crear parametros adicionales necesarios para determinada estrategia
        self._additional_parameters[b_index] = dict()

        # itera sobre Technical y Breakout (las estrategias).
        for strat, params in self._extra_params.items():
            # Itera sobre los diccionarios dentro de Technical y Breakout
            for param in params:
                self._additional_parameters[b_index][param['code_name']] = None


        self._body_index += 1

    def _show_popup(self, b_index: int):

        # Acá tomamos las coordenadas del botón que presionamos (parameters) para que el popup salga arriba de él
        # y no en cualquier lado
        x = self.body_widgets["parameters"][b_index].winfo_rootx()
        y = self.body_widgets["parameters"][b_index].winfo_rooty()

        # Toplevel sirve para laburar con popups
        # Vamos a crear una nueva ventana que aparecerá al presionar el botón de parameters, y en la cual
        # podremos definir parámetros para la estrategia que elegimos.
        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title("Parameters")
        self._popup_window.config(bg=BG_COLOR)
        # -topmost se usa para que la nueva ventana quede "por encima" de la pantalla actual mientras esté abierta
        self._popup_window.attributes("-topmost", "true")
        # nos asegura que sólo podamos clickear en la ventana del popup (no en la otra) mientras está abierta
        self._popup_window.grab_set()

        # esto se hace para asociar las coordinadas que tomará el popup y moverlo unos píxeles (-80 +30) para que se
        # vea el botón de parameters
        self._popup_window.geometry(f"+{x - 80}+{y + 30}")

        # Identifico la estrategia utilizada para crear los inputs de los parameters dinámicamente (en base a la
        # estrategia)
        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        # variable para iterar fila a fila a través de la etiqueta creada y llenarla con los parámetros que irán
        # de acuerdo a la estrategia seleccionada

        row_nb = 0

        for param in self._extra_params[strat_selected]:
            # itero los parámetros a través de la etiqueta
            code_name = param['code_name']
            temp_label = tk.Label(self._popup_window, bg=BG_COLOR, fg=FG_COLOR, text=param['name'], font=BOLD_FONT)
            temp_label.grid(row = row_nb, column=0)

            if param['widget'] == tk.Entry:
                self._extra_input[code_name] = tk.Entry(self._popup_window, bg=BG_COLOR2, justify=tk.CENTER, fg=FG_COLOR,
                                      insertbackground=FG_COLOR)

                if self._additional_parameters[b_index][code_name] is not None :
                    self._extra_input[code_name].insert(tk.END, str(self._additional_parameters[b_index][code_name]))

            else:
                continue

            self._extra_input[code_name].grid(row=row_nb, column=1)

            row_nb += 1

        # Botón de validación del label de los parámetros de cada estrategia

        validation_button = tk.Button(self._popup_window, text="Validate", bg=BG_COLOR2, fg=FG_COLOR,
                                      command=lambda: self._validate_parameters(b_index))

        # se agrega al final tras las labels de parámetros, empieza en la columna 0 y se expande 2 columnas
        # (queda centrado así)
        validation_button.grid(row=row_nb, column=0, columnspan=2)


    def _validate_parameters(self, b_index: int):

        # Identifico la estrategia utilizada para crear los inputs de los parameters dinámicamente (en base a la
        # estrategia)
        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strat_selected]:
            code_name = param['code_name']

            if self._extra_input[code_name].get() == "":
                self._additional_parameters[b_index][code_name] = None
            else :
                self._additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].get())

        # cuando presionamos el botón de validate del popup de parámetros, se borra la ventana de popup
        self._popup_window.destroy()



    # Tendrá 2 funcionalidades:
    # Una para activar o desactivar la estrategia
    # Una para confirmar que todos los parámetros requeridos de la estrategia fueron ingresados para poder activarla.
    def _switch_strategy(self, b_index: int):

        # chequeamos los 3 parámetros comunes a cualquier estrategia
        for param in ["balance_pct", "take_profit", "stop_loss"]:
            # Si ese entry devuelve vacío, es decir que nada de eso tiene datos, quiere decir que no completé
            # la estrategia correctamente, por ende, no permitirá ingresarla y devolverá con el return
            if self.body_widgets[param][b_index].get() == "":
                self.root.logging_frame.add_log(f"Missing {param} parameter")
                return

        # Ahora viene la parte para chequear que todos los parámetros particulares de cada estrategia sean
        # completados por el usuario
        strat_selected = self.body_widgets['strategy_type_var'][b_index].get()

        for param in self._extra_params[strat_selected]:
            if self._additional_parameters[b_index][param['code_name']] is None:
                self.root.logging_frame.add_log(f"Missing {param['code_name']} parameter")
                return

        # Si están completados todos los parámetros requeridos, avanzo y los guardo
        # Por ejemplo el symbol BTCUSDT_BINANCE , la primer parte [0] es el contrato y la segunda el exchange
        symbol = self.body_widgets['contract_var'][b_index].get().split("_")[0]
        exchange = self.body_widgets['contract_var'][b_index].get().split("_")[1]

        timeframe = self.body_widgets['timeframe_var'][b_index].get()
        balance_pct = float(self.body_widgets['balance_pct'][b_index].get())
        take_profit = float(self.body_widgets['take_profit'][b_index].get())
        stop_loss = float(self.body_widgets['stop_loss'][b_index].get())

        # Si el botón está en OFF
        if self.body_widgets['activation'][b_index].cget("text") == "OFF":
            # Activar estrategia
            for param in self._base_params:
                code_name = param['code_name']
                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state= tk.DISABLED)

            # cambio el color y valor del botón clickeado (ya que quedó disabled)
            self.body_widgets["activation"][b_index].config(bg= "darkgreen", text= "ON")
            self.root.logging_frame.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} started")

        else:
            # Desactivar estrategia
            for param in self._base_params:
                code_name = param['code_name']
                if code_name != "activation" and "_var" not in code_name:
                    self.body_widgets[code_name][b_index].config(state= tk.NORMAL)

            # cambio el color y valor del botón clickeado (ya que quedó disabled)
            self.body_widgets["activation"][b_index].config(bg= "darkred", text= "OFF")
            self.root.logging_frame.add_log(f"{strat_selected} strategy on {symbol} / {timeframe} stopped")


        return

    def _delete_row(self, b_index: int):

        for element in self._base_params:
            self.body_widgets[element['code_name']][b_index].grid_forget()
            del self.body_widgets[element['code_name']][b_index]
