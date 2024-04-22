# models se refiere al data model de python. En este caso crearemos clases para manejar
# los datos que se obtienen, agrupados en una clase, y poder manejarlos mas fácil que con
# solo diccionarios.

# https://binance-docs.github.io/apidocs/testnet/en/#account-information-v2-user_data

# Defino una variable global para bitmex, ya que este exchange da los balances en satoshis.
# Entonces defino el valor para la equivalencia con BTC 1 satoshi = 0.00000001 BTC
BITMEX_MULTIPLIER = 0.00000001

class Balance:
    def __init__(self, info, exchange):

        if exchange == "binance":
            self.initial_margin = float(info['initialMargin'])
            self.maintenance_margin = float(info['maintMargin'])
            self.margin_balance = float(info['marginBalance'])
            self.wallet_balance = float(info['walletBalance'])
            self.unrealized_pnl = float(info['unrealizedProfit'])

        elif exchange == "bitmex":
            self.initial_margin = info['initMargin'] * BITMEX_MULTIPLIER
            self.maintenance_margin = info['maintMargin'] * BITMEX_MULTIPLIER
            self.margin_balance = info['marginBalance'] * BITMEX_MULTIPLIER
            self.wallet_balance = info['walletBalance'] * BITMEX_MULTIPLIER
            self.unrealized_pnl = info['unrealisedPnl'] * BITMEX_MULTIPLIER


class Candle:
    def __init__(self, candle_info):
        self.timestamp = candle_info[0]
        self.open = float(candle_info[1])
        self.high = float(candle_info[2])
        self.low = float(candle_info[3])
        self.close = float(candle_info[4])
        self.volume = float(candle_info[5])

# Al implementar otro exchange extra (en este caso Bitmex) el Contract que devuelva el request, va a traer datos,
# pero su estructura es diferente: así , si bien tendrá un symbol, base asset, etc, los nombres dentro del diccionario
# ('') van a ser diferentes, por ejemplo  self.base_asset = contract_info['Asset'] podría ser así.
# entonces necesito meter un if para identificar el exchange previo a la devolución que haga esta clase
class Contract:
    def __init__(self, contract_info, exchange):
        if exchange == "binance":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['baseAsset']
            self.quote_asset = contract_info['quoteAsset']
            # Estos últimos 2 se usan para redondear precio y cantidad de una orden a un decimal aceptado por Binance
            self.price_decimals = contract_info['pricePrecision']
            self.quantity_decimals = contract_info['quantityPrecision']

        elif exchange == "bitmex":
            self.symbol = contract_info['symbol']
            self.base_asset = contract_info['rootSymbol']
            self.quote_asset = contract_info['quoteCurrency']
            # Estos últimos 2 se usan para redondear precio y cantidad de una orden a un decimal aceptado por Binance
            self.price_decimals = contract_info['tickSize']
            self.quantity_decimals = contract_info['lotSize']


class Contract_Bitmex:
    def __init__(self, contract_info):
        self.symbol = contract_info['symbol']
        self.root_symbol = contract_info['rootSymbol']

class OrderStatus:
    def __init__(self, order_info):
        self.order_id = order_info['orderId']
        self.status = order_info['status']
        self.avg_price = float(order_info['avgPrice'])