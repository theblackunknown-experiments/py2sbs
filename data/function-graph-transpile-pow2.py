"""Function graph declaration, transpiling pow function to pow2 after analyzing that base is a constant expression equals to 2"""

def pow(exponent, x = 5):
    return 2 ** exponent
