import pandas as pd

from mammoth.models.model import Model
from loader_data_csv_rankings import data_csv_rankings


class Ranking(Model):
    def __init__(self, path: str):
        self.model_url = path

    def normal_ranking(self, path: str, ranking_variable: str = 'citations') -> pd.DataFrame:
        """
        Perform ranking without considering any protected attribute and using only one variable.

        Args:
        path (str): Path to the dataset CSV file.
        ranking_variable (str): Variable to use for ranking.

        Returns:
        pd.DataFrame: DataFrame with rankings based on the specified variable.
        """
        # Load the dataset
        dataset = data_csv_rankings(path)
        
        # Perform the ranking
        ranked_dataframe = dataset.sort_values(ranking_variable)
        ranked_dataframe['Ranking'] = [i + 1 for i in range(ranked_dataframe.shape[0])]
        
        return ranked_dataframe
