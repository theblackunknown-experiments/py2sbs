"""Sample 00 - showcase how function definition turn into FunctionGraph"""

def add(x, y):
    return x + y

def mod(x, y : int):
    return x % y

def pow(exponent, base = 2, x = 5):
    return base ** exponent

def color_pixelprocessor():
    return ( 1.0, 0.0, 1.0, 1.0 )

def grayscale_pixelprocessor():
    return 0.5
