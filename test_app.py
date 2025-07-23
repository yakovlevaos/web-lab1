import numpy as np
from app import swap_stripes

def test_horizontal_swap():
    img = np.arange(4 * 2 * 3).reshape(4, 2, 3)
    result = swap_stripes(img, 'horizontal', 1)
    assert np.array_equal(result[0], img[1])
    assert np.array_equal(result[1], img[0])

def test_vertical_swap():
    img = np.arange(2 * 4 * 3).reshape(2, 4, 3)
    result = swap_stripes(img, 'vertical', 1)
    assert np.array_equal(result[:, 0], img[:, 1])
    assert np.array_equal(result[:, 1], img[:, 0])
