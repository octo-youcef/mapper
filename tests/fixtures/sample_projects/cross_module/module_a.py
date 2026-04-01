"""Module A - imports from module B and external packages."""

import module_b  # Internal import
import pandas as pd


def process_with_b(data):
    """Process data using module B."""
    result = module_b.transform(data)
    df = pd.DataFrame(result)
    return df


def helper():
    """Helper function."""
    return "helper"
