
import pandas as pd
from mammoth.models.model import Model
from loader_data_csv_rankings import data_csv_rankings


class RANKINGS(Model):
    def __init__(self, path: str):
        self.model_url = path

    def normal_ranking(self,path,ranking_variable='citations'):
        '''Ranking without considering any prottected attribute and just one variable
    '''
        path = 'https://github.com/anajaramillo37/mammoth-commons/tree/dev/data/researchers/Top_researchers.csv'
        dataframe = data_csv_rankings(path)
        Rankend_dataframe = dataframe.sort_values(ranking_variable, ascending=False)
        Rankend_dataframe['Ranking_'+ranking_variable] = [i+1 for i in range(Rankend_dataframe.shape[0])]
      
        return Rankend_dataframe
