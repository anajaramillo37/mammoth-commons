
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

    def Compute_mitigation_strategy(path, model, mitigation_method, sampling_attribute, ranking_variable, sensitive_attribute, protected_attribute, n_runs)::

    dataset = pd.read_csv(path, delimiter='|')
    Dataframe_ranking = model(dataset,ranking_variable)
    Dataframe_ranking = Dataframe_ranking[~Dataframe_ranking[sampling_attribute].isnull()]

    ranking = 'Ranking_'+ranking_variable

    ERr_list = {}

    for r in range(n_runs):
        print(r)
        Chosen_groups, Chosen_researchers = {}, {}

        for category in set(Dataframe_ranking[sampling_attribute]):
            Dataframe_ranking_filtered = Dataframe_ranking[Dataframe_ranking[sampling_attribute]==category]
            Dataframe_ranking_filtered = Dataframe_ranking_filtered[~Dataframe_ranking_filtered[sensitive_attribute].isnull()]
            sensitive = set(Dataframe_ranking_filtered[sensitive_attribute])

            Ranking_sets  = {attribute: Dataframe_ranking_filtered[Dataframe_ranking_filtered[sensitive_attribute] == attribute] for attribute in sensitive}

            if Method == 'Statistical_parity':
                P_minority = Dataframe_ranking_filtered[Dataframe_ranking_filtered[sensitive_attribute] == protected_attribute].shape[0]/Dataframe_ranking_filtered.shape[0]
            elif Method == 'Equal_parity':
                P_minority = 0.5
            elif Method == 'Updated_statistical_parity':
                print('In construction')
            elif Method == 'Internal_group_fairness':
                print('In construction')


            non_protected_attribute = [i for i in sensitive if i != protected_attribute][0]
            Min_size = min(len(Ranking_sets[protected_attribute]), len(Ranking_sets[protected_attribute]))

            Chosen_groups[category] = [choices([protected_attribute,non_protected_attribute], [P_minority,1-P_minority])[0] for i in range(Min_size)]



            Positions = {non_protected_attribute: [i for i in range(Min_size) if Chosen_groups[category][i] == non_protected_attribute],
                     protected_attribute: [i for i in range(Min_size) if Chosen_groups[category][i] == protected_attribute]}

            Chosen_researchers[category] = {i_ranking:Ranking_sets[non_protected_attribute].iloc[i_position]['id'] for i_position,i_ranking in enumerate(Positions[non_protected_attribute])}
            for i_position,i_ranking in enumerate(Positions[protected_attribute]):
                Chosen_researchers[category][i_ranking] = Ranking_sets[protected_attribute].iloc[i_position]['id']

            Chosen_researchers[category] = dict(OrderedDict(sorted(Chosen_researchers[category].items(), key=lambda t: t[0])))

        List_Chosen_groups = [] 
        List_Chosen_rankings = []
        List_Chosen_researchers = []
        List_category = []

        for category in set(Dataframe_ranking[sampling_attribute]):
            List_Chosen_groups +=  Chosen_groups[category]
            List_Chosen_rankings += list(Chosen_researchers[category].keys())
            List_Chosen_researchers += list(Chosen_researchers[category].values())
            List_category += [category]*len(list(Chosen_researchers[category].values()))

        New_ranking_DDBB = pd.DataFrame({sensitive_attribute: List_Chosen_groups, 
                                         ranking: List_Chosen_rankings,
                                         sampling_attribute:List_category,
                                         'Researcher_id':List_Chosen_researchers})

        df = New_ranking_DDBB

        df_non_protected_attribute = df[df[sensitive_attribute]==non_protected_attribute]
        df_protected_attribute = df[df[sensitive_attribute]==protected_attribute]

        df_filtered = {sensitive_attribute:[], ranking:[], sampling_attribute: [], 'Researcher_id': []}

        for category in set(Dataframe_ranking[sampling_attribute]):
            Min_size = min(len(list(df_non_protected_attribute[df_non_protected_attribute[sampling_attribute] == category][ranking])), len(list(df_protected_attribute[df_protected_attribute[sampling_attribute] == category][ranking])))
            df_filtered[sampling_attribute] += [category]*Min_size*2
            df_filtered[sensitive_attribute] += [non_protected_attribute]*Min_size+[protected_attribute]*Min_size
            df_filtered[ranking] += list(df_non_protected_attribute[df_non_protected_attribute[sampling_attribute] == category][ranking])[:Min_size]+list(df_protected_attribute[df_protected_attribute[sampling_attribute] == category][ranking])[:Min_size]
            df_filtered['Researcher_id'] += list(df_non_protected_attribute[df_non_protected_attribute[sampling_attribute] == category].Researcher_id)[:Min_size]+list(df_protected_attribute[df_protected_attribute[sampling_attribute] == category].Researcher_id)[:Min_size]
        df_filtered = pd.DataFrame(df_filtered)
