from mammoth.exports import Markdown
from mammoth.integration import metric
from loader_data_csv_rankings import data_csv_rankings
from Rankings import RANKINGS
import seaborn as sns
import numpy as np


class Fairness_metrics_in_rankings:
    def __init__(self, path: str, EDr):
        self.model_url = path
        self.EDr = EDr

    def b(k):
        '''Function defining the position bias: the highest ranked candidates receive more attention from users than candidates at lower ranks, and here is adoptedwith algorithmic discount with smooth reduction and favorable theoretical properties (https://proceedings.mlr.press/v30/Wang13.html).'''
        return 1 / np.log2(k + 1)

    def Exposure_distance(self,
                          path,
                          model,
                          ranking_variable,
                          sensitive_attribute,
                          protected_attirbute,
                          sampling_attribute):
        '''Exposure distance to see where are the two groups located in the ranking'''
        dataset = data_csv_rankings(path)
        Dataframe_ranking = model(dataset,ranking_variable)
        Dataframe_ranking = Dataframe_ranking[~Dataframe_ranking[sampling_attribute].isnull()]

        EDr = {}
        for category in set(Dataframe_ranking[sampling_attribute]):
            Dataframe_ranking_filtered = Dataframe_ranking[Dataframe_ranking[sampling_attribute]==category]
            Dataframe_ranking_filtered = Dataframe_ranking_filtered[~Dataframe_ranking_filtered[sensitive_attribute].isnull()]
            sensitive_attribute ='Gender'
            rankings_per_attribute = {}
            ranking = 'Ranking_'+ranking_variable
            sensitive = list(set(Dataframe_ranking_filtered[sensitive_attribute]))
            try:
                assert len(sensitive) == 2
                for attribute_value in sensitive:
                    rankings_per_attribute[attribute_value] = list(Dataframe_ranking_filtered[Dataframe_ranking_filtered[attribute] == attribute_value][ranking]
                                                            )
    
                non_protected_attribute = [i for i in sensitive if i != protected_attirbute][0]
    
                ranking_position_protected_attribute = [b(1 / (r + 1)) for r in rankings_per_attribute[protected_attirbute]]
                ranking_position_non_protected_attribute = [b(1 / (r + 1)) for r in rankings_per_attribute[non_protected_attribute]]
    
                Min_size = min(len(ranking_position_protected_attribute), len(ranking_position_non_protected_attribute))
                EDr[category] = np.round((sum(ranking_position_protected_attribute[:Min_size]) - sum(ranking_position_non_protected_attribute[:Min_size])), 2)
            except:
                EDr[category] = np.nan
        return EDr

    def create_box_plot_rankings(dataframe, hue_variable, ranking_variable, y_variable):  
        width = 0.6, font_size_out = 14, nrows = 1, ncols = 1
        fig, ax = plt.subplots(ncols=ncols, nrows=nrows,figsize=(5*ncols,3*nrows), sharex= True, sharey= False,
                               gridspec_kw={'width_ratios': [1]*ncols})
    
        sns.boxplot(data=dataframe, x=ranking_variable, y=y_variable, 
                    hue=hue_variable,
                    saturation=0.8,linewidth=0.75, ax = ax)
    
    
        for spine in ['right', 'top']:
            ax.spines[spine].set_visible(False)
    
        ax.tick_params('x', size=5, colors="black", labelsize=font_size_out+4)
        ax.tick_params('y', size=5, colors="black", labelsize=font_size_out+1)
    
        ax.set_ylabel(' ',  size=0)
        ax.set_xlabel(ranking_variable,  size=font_size_out+6)
    
        ax.legend(bbox_to_anchor=(1.05, 1.05))
    
        plt.subplots_adjust(wspace=0.2, hspace=0.1)
        plt.show()


@metric(namespace="mammotheu", version="v003", python="3.11")
def ExposureDistance(
        dataset: data_csv_rankings,
        model: RANKINGS.normal_ranking,
        sensitive: str = 'Gender'
) -> Markdown:
    '''Compute the exposure distance  '''

    EDr = Fairness_metrics_in_rankings.Exposure_distance(dataset, model, sensitive)

    return Markdown(text=str(EDr))


