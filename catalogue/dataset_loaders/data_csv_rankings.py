import os.path
from mammoth.datasets import CSV
from mammoth.integration import loader
import fairbench as fb
import pandas as pd
from typing import List, Optional

@loader(namespace="mammotheu", version="v0020", python="3.11")
def load_csv_dataset(
    path: str = "",
    numeric: List[str] = ["Ranking", "Value"],
    categorical: List[str] = ["Gender", "Nationality"],
    labels: Optional[str] = None,
    delimiter: str = ",",
    on_bad_lines: str = "skip",
) -> CSV:
    """
    Load a CSV dataset.

    :param path: The path to the CSV file
    :param numeric: List of numeric column names
    :param categorical: List of categorical column names
    :param labels: Optional label column name
    :param delimiter: The delimiter of the CSV file
    :param on_bad_lines: How to handle bad lines in the CSV file
    :return: The loaded CSV data as a CSV object
    """
    if not path.endswith(".csv"):
        raise ValueError("Invalid file format. Only CSV files are supported.")
    
    raw_data = pd.read_csv(path, delimiter=delimiter, error_bad_lines=on_bad_lines)
    return raw_data
