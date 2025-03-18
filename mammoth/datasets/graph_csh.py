from mammoth.datasets.dataset import Dataset


class Graph_CSH(Dataset):
    """
    A class to represent a co-authorship graph based on a dataset of papers and their affiliations.

    Attributes:
        papers_df (DataFrame): DataFrame containing information about papers.
        affiliations_df (DataFrame): DataFrame containing information about authors and their affiliations.
        G (NetworkX Graph): The co-authorship graph constructed from the input data.
        cols (list): List of sensitive columns to consider in the analysis.
    """
    
    def __init__(self, papers_df, affiliations_df, sensitive_columns=[]):
        """
        Initializes the Graph object with the provided DataFrames and sensitive columns.

        Parameters:
            papers_df (DataFrame): DataFrame containing information about papers.
            affiliations_df (DataFrame): DataFrame containing information about authors and their affiliations.
            sensitive_columns (list): Optional list of sensitive columns to consider in the analysis.
        """
        
        self.papers_df = papers_df # DataFrame with papers data
        self.affiliations_df = affiliations_df # DataFrame with affiliations data
        self.G = None # Placeholder for the co-authorship graph
        self.cols = sensitive_columns # Sensitive columns to be used in the analysis


    def create_coauth_graph(self):
        """
        Creates a co-authorship graph based on the papers and affiliations data.

        This method constructs a network of authors based on their co-authorships,
        computes weights for each edge and adds various metrics to the graph nodes
        such as citations, productivity, and degree. The resulting graph is stored
        in the G attribute.
        """
        
        import networkx as nx
        import numpy as np

        # Dictionaries to store links between authors and papers
        Authors_papers_links = {}
        Papers_authors_links = {}

        DF_Affiliations = self.affiliations_df

        # Populate authors and papers links
        for i in self.affiliations_df.index:
            try:
                Authors_papers_links[DF_Affiliations["researcher_id"][i]].add(
                    DF_Affiliations["doi"][i]
                )
            except:
                Authors_papers_links[DF_Affiliations["researcher_id"][i]] = set(
                    [DF_Affiliations["doi"][i]]
                )

            try:
                Papers_authors_links[DF_Affiliations["doi"][i]].add(
                    DF_Affiliations["researcher_id"][i]
                )
            except:
                Papers_authors_links[DF_Affiliations["doi"][i]] = set(
                    [DF_Affiliations["researcher_id"][i]]
                )

        # Initialize co-authorship links
        Co_authorship_links = {}

        # Create co-authorship pairs
        for k in Authors_papers_links.keys():
            Co_authorship_links[k] = {}

        for doi in Papers_authors_links.keys():
            authors = Papers_authors_links[doi]
            for k1 in authors:
                for k2 in authors:
                    if k1 != k2:
                        try:
                            Co_authorship_links[k1][k2]["papers"].add(doi)
                        except:
                            Co_authorship_links[k1][k2] = {"papers": set([doi])}

                        try:
                            Co_authorship_links[k2][k1]["papers"].add(doi)
                        except:
                            Co_authorship_links[k2][k1] = {"papers": set([doi])}

        # Compute the weights of the network:
        for u in Co_authorship_links.keys():
            for v in Co_authorship_links[u].keys():
                Co_authorship_links[u][v]["weight"] = len(
                    Co_authorship_links[u][v]["papers"]
                )

        # Create the co-authorship network graph
        Couthorship_network = nx.Graph(Co_authorship_links)
        Couthorship_network.remove_node(np.nan) # Remove any nodes with NaN

        # Add attributes to the nodes based on paper metrics:
        for u in Couthorship_network.nodes():
            Filtered_DF = self.papers_df[
                self.papers_df.doi.isin(Authors_papers_links[u])
            ]

            # 0. Add protected attributes:
            max_year = self.papers_df.loc[Filtered_DF.year.idxmax()]["year"]
            Filtered_affiliation = DF_Affiliations[
                (DF_Affiliations.year == max_year)
                & (DF_Affiliations.researcher_id == u)
            ]
            for attribute in ["Nationality", "aff_country", "Gender"]:
                Couthorship_network.nodes[u][attribute] = Filtered_affiliation.iloc[0][
                    attribute
                ]

                if attribute != "Gender":
                    for category in ["Region", "IncomeGroup"]:
                        Couthorship_network.nodes[u][attribute + "_" + category] = (
                            Filtered_affiliation.iloc[0][attribute + "_" + category]
                        )

            # 1. Analyze the rankings for citations, productivity, and degree
            Citations = sum(Filtered_DF.N_citations) # Total citations for the author
            Productivity = len(Authors_papers_links[u]) # Number of papers authored
            Degree = sum(
                [
                    Couthorship_network[u][v]["weight"]
                    for v in Couthorship_network[u].keys()
                ]
            ) # Total co-authorship connections
            Couthorship_network.nodes[u]["Citations"] = Citations
            Couthorship_network.nodes[u]["Productivity"] = Productivity
            Couthorship_network.nodes[u]["Degree"] = Degree

        self.G = Couthorship_network # Store the constructed graph

    def return_num_nodes(self):
        """
        Returns the number of nodes (papers) in the papers DataFrame.

        Returns:
            int: The number of nodes (papers) in the dataset.
        """
        
        return self.papers_df.shape[0] # Number of papers

    def return_num_edges(self):
        """
        Returns the number of edges (affiliations) in the affiliations DataFrame.

        Returns:
            int: The number of edges (affiliations) in the dataset.
        """
        
        return self.affiliations_df.shape[0] # Number of affiliations
