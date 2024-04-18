# models se refiere al data model de python. En este caso crearemos clases para manejar
# los datos que se obtienen, agrupados en una clase, y poder manejarlos mas fácil que con
# solo diccionarios.

# https://binance-docs.github.io/apidocs/testnet/en/#account-information-v2-user_data
class Balance:
    def __init__(self, info):
        self.initial_margin = float(info['initialMargin'])
        self.maintenance_margin = float(info['maintMargin'])
        self.margin_balance = float(info['marginBalance'])
        self.wallet_balance = float(info['walletBalance'])
        self.unrealized_pnl = float(info['unrealizedProfit'])

class Candle:
    def __init__(self, candle_info):
        self.timestamp = candle_info[0]
        self.open = float(candle_info[1])
        self.high = float(candle_info[2])
        self.low = float(candle_info[3])
        self.close = float(candle_info[4])
        self.volume = float(candle_info[5])

class Contract:
    def __init__(self, contract_info):
        self.symbol = contract_info['symbol']
        self.base_asset = contract_info['baseAsset']
        self.quote_asset = contract_info['quoteAsset']

        # Estos últimos 2 se usan para redondear precio y cantidad de una orden a un decimal aceptado por Binance
        self.price_decimals = contract_info['pricePrecision']
        self.quantity_decimals = contract_info['quantityPrecision']

class OrderStatus:
    def __init__(self, order_info):
        self.order_id = order_info['orderId']
        self.status = order_info['status']
        self.avg_price = float(order_info['avgPrice'])