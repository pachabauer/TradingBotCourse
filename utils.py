# En este módulo implementaré funciones para chequear que los datos introducidos por el usuario en el entry
# sean lógicos: por ejemplo, donde va un float el usuario no podrá escribir un string, etc.

def check_integer_format(text: str):
    if text == "":
        return True

    # Si todos los caracteres del int contienen alguno de estos caracteres, avanzo (es un int).
    if all(x in "0123456789" for x in text):
        try:
            int(text)
            return True
        except ValueError:
            return False

    else:
        return False


def check_float_format(text: str):
    if text == "":
        return True

    # Si todos los caracteres del float contienen alguno de estos caracteres, avanzo (es un float).
    # además solo debe contener un decimal (no más de eso).
    if all(x in "0123456789." for x in text) and text.count(".") <= 1:
        try:
            float(text)
            return True
        except ValueError:
            return False

    else:
        return False
