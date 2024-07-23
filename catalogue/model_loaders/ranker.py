from mammoth.datasets import CSV
from mammoth.exports import Markdown
from typing import Dict, List
from mammoth.integration import metric, loader
from loader_data_csv_rankings import data_csv_rankings
from mammoth.datasets.rankings import normal_ranking


@loader(namespace="mammotheu", version="v003", python="3.11")
def load_normal_ranking_model(
    path: str,
    ranking_variable: str
) -> normal_ranking:
    """
    Load a normal ranking model.

    :param path: The path to the model file.
    :param ranking_variable: The variable used for ranking.
    :return: The loaded normal ranking model.
    """
    return normal_ranking(path, ranking_variable)
