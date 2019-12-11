
import sbs

@sbs.pixelprocessor
def color_pixelprocessor():
    return ( 1.0, 0.0, 1.0, 1.0 )

@sbs.pixelprocessor
def grayscale_pixelprocessor():
    return 0.5
