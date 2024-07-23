from mammoth.exports import Markdown
from mammoth.integration import metric
from mammoth.datasets import ranking
from mammoth.catalogue import data_csv_rankings
import numpy as np


class FairnessMetricsInRankings:
    def __init__(self, path: str, edr: float):
        """
        Initialize FairnessMetricsInRankings object with the specific path and exposure distance.

        :param path: The path of the model.
        :param EDr: The exposure distance value.
        """
        self.model_url = path
        self.edr = edr

    @staticmethod
    def b(k: int) -> float:
        '''
        Function defining the position bias: adopted with algorithmic discount for smooth reduction and favorable properties.

        Reference: https://proceedings.mlr.press/v30/Wang13.html
        '''
        return 1 / np.log2(k + 1)

    @metric(namespace="mammotheu", version="v003", python="3.11")
    def exposure_distance(self, dataset: data_csv_rankings, model: ranking.normal_ranking, sensitive: str = 'Gender') -> float:
        '''
        Compute the exposure distance to locate the two groups in the ranking.

        :param path: The path of the dataset.
        :param model: The model used for ranking.
        :param sensitive: A list containing sensitive attribute values.
        :return: The calculated Exposure Distance.
        '''
       
        
        dataset = data_csv_rankings(path)
        dataframe_ranking = model(dataset, 'Value')

        groups_sensitive_attribute = set(dataframe_ranking[sensitive])

         assert len(groups_sensitive_attribute) == 2

        rankings_per_attribute = {}
        for attribute in groups_sensitive_attribute:
            rankings_per_attribute[attribute] = list(dataframe_ranking[dataframe_ranking[attribute] == attribute].Ranking)

        self.edr = np.round((sum([self.b(1 / (r + 1)) for r in rankings_per_attribute[sensitive[0]]) 
                            - sum([self.b(1 / (r + 1)) for r in rankings_per_attribute[sensitive[1]])) / dataframe_ranking.shape[0], 2)

        return Markdown(text=str(self.edr))
