import sqlite3
import typing


class WorkspaceData:
    def __init__(self):
        # conexión con la base de datos (usaremos sqllite)
        self.conn = sqlite3.connect("database.db")
        # Acá le digo que cuando obtenga data de la db , devuelva una lista de Row objects, que en python pueden
        # accederse como diccionarios (lo cual es mucho más conveniente que como vienen por default,
        # una lista de tuplas).
        self.conn.row_factory = sqlite3.Row
        # hace las queries a la db
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT, exchange TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS strategies (strategy_type TEXT, contract TEXT,"
                            "timeframe TEXT, balance_pct REAL, take_profit REAL, stop_loss REAL, extra_params TEXT)")

        self.conn.commit()

    # este método guarda la información en la db: necesita el nombre de la tabla y la lista de tuplas (Row) que
    # quiero guardar
    def save(self, table: str, data: typing.List[typing.Tuple]):
        # primero debo borrar lo que tenía la tabla para guardar los nuevos cambios
        self.cursor.execute(f"DELETE FROM {table}")

        table_data = self.cursor.execute(f"SELECT * FROM {table}")

        # Esto crea una lista de columnas
        columns = [description[0] for description in table_data.description]

        # sentencia sql
        # el primer join convierte la lista de columnas a string donde cada elemento de la columna ahora está separado
        # por una coma. El segundo join hace lo mismo, pero crea de forma dinámica la cantidad de columnas en base
        # a lo cantidad de elementos que posea la lista
        sql_statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES({', '.join(['?'] * len(columns))})"

        # inserta varias líneas en la tabla a la vez
        self.cursor.executemany(sql_statement, data)
        self.conn.commit()

    # get data de la tabla
    def get(self, table: str) -> typing.List[sqlite3.Row]:
        self.cursor.execute(f"SELECT * FROM {table}")
        data = self.cursor.fetchall()

        # devuelve una lista de sql3lite Row Objects y estos objetos pueden accederse como python dictionaries
        return data
