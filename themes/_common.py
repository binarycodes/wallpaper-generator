import numpy as np


def unit(im):
    """Greyscale image as a float array in 0..1."""
    return np.asarray(im).astype(np.float32) / 255


def luminance(rgb):
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
