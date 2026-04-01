"""Module B - imports from module C."""

import module_c  # Internal import
import numpy as np


def transform(data):
    """Transform data using module C."""
    validated = module_c.validate(data)
    array = np.array(validated)
    return array.tolist()


def process():
    """Process function."""
    return module_c.validate([1, 2, 3])
