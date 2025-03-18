from typing import List

import mammoth.integration
from mammoth.exports import Markdown, HTML
from mammoth.integration import metric
from mammoth.models.researcher_ranking import ResearcherRanking
from mammoth.datasets.csv import CSV
from mammoth.datasets.graph_csh import Graph_CSH
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import statistics
from . import networks_layouts
import networkx as nx


def b(k):
    """Calculate the position bias based on the rank of candidates.

    The position bias reflects the idea that higher-ranked candidates receive more attention from users than those at lower ranks.
    This function implements an algorithmic discount where the attention given to a candidate decreases logarithmically with its rank.
    The implementation follows the principles described in the paper "Position Bias in Information Retrieval" 
    (https://proceedings.mlr.press/v30/Wang13.html), emphasizing a smooth reduction in attention with favorable theoretical properties.
    
    Args:
        k (int or float): The rank (1-based index) of the candidate. Must be a non-negative integer.
        
    Returns:
        float: The position bias value for the given rank, computed as 1 divided by the logarithm base 2 of (k + 1).
               This results in higher values for lower ranks and decreases logarithmically as the rank increases.
    """
    # Returning the position bias value calculated using the logarithmic formula.
    return 1 / np.log2(k + 1)


def Exposure_distance(
    dataset, ranking_variable, sensitive_attribute, protected_attirbute
):
   """
    Calculate the exposure distance between two groups based on a ranking variable.

    This function computes the difference in rankings between a protected attribute group
    and a non-protected attribute group to assess their relative positioning in the rankings.

    Parameters:
    dataset (DataFrame): A pandas DataFrame containing the data to analyze.
    ranking_variable (str): The name of the ranking variable column to evaluate.
    sensitive_attribute (str): The name of the column that indicates the sensitive attribute (e.g., gender).
    protected_attirbute (str): The value of the sensitive attribute that is considered protected.

    Returns:
    float: The exposure distance (EDr) between the two groups, or NaN if an exception occurs.
    """

    # Remove rows with missing values in the sensitive attribute
    # This step ensures that only complete entries for the sensitive_attribute are considered
    dataset = dataset[~dataset[sensitive_attribute].isnull()] # Filter out NaN or None values

    rankings_per_attribute = {}  # Dictionary to hold rankings for each attribute value
    sensitive = list(set(dataset[sensitive_attribute])) # Unique values of the sensitive attribute
    try:
        assert len(sensitive) == 2 # Ensure there are exactly two groups to compare

         # Populate the rankings_per_attribute dictionary
        for attribute_value in sensitive:
            rankings_per_attribute[attribute_value] = list(
                dataset[dataset[sensitive_attribute] == attribute_value][
                    "Ranking_" + ranking_variable
                ]
            )

        # Identify the non-protected attribute group
        non_protected_attribute = [i for i in sensitive if i != protected_attirbute][0]

        # Compute ranking positions for the protected and non-protected attributes
        ranking_position_protected_attribute = [
            b(1 / (r + 1)) for r in rankings_per_attribute[protected_attirbute]
        ]
        ranking_position_non_protected_attribute = [
            b(1 / (r + 1)) for r in rankings_per_attribute[non_protected_attribute]
        ]

        # Determine the minimum size for comparison to prevent index errors
        Min_size = min(
            len(ranking_position_protected_attribute),
            len(ranking_position_non_protected_attribute),
        )

        # Calculate the exposure distance (EDr)
        EDr = np.round(
            (
                sum(ranking_position_protected_attribute[:Min_size])
                - sum(ranking_position_non_protected_attribute[:Min_size])
            ),
            2,
        )
        
    except Exception as e:
        print("Exception") # Print the exception for debugging
        EDr = np.nan # Set exposure distance to NaN if an error occurs
    return EDr


def boxplots_rankings(dataframe, hue_variable, ranking_variable, y_variable):
    """
    Create and display a boxplot for the specified ranking and y variables, 
    differentiated by the hue variable. The plot adapts its height based on 
    the number of unique categories in the y variable. 

    Parameters:
    - dataframe (pd.DataFrame): The source dataset containing the data to plot.
    - hue_variable (str): The name of the column in the dataframe to use for color encoding (hue).
    - ranking_variable (str): The name of the column in the dataframe that represents the ranking.
    - y_variable (str): The name of the column in the dataframe to be displayed on the y-axis.

    Returns:
    - str: A base64 encoded string representation of the generated plot image.
    """
    
    # Set figure size based on the number of unique categories in the y_variable
    n_categories = len(dataframe[y_variable].unique())
    height = min(7, max(4, n_categories * 0.5))  # # Adaptive height between 4 and 7 inches

    # Enable tight layout for the figure
    plt.rcParams["figure.autolayout"] = True

    # Create a new figure and axis with specified size
    fig, ax = plt.subplots(figsize=(8, height), constrained_layout=True)

    # Create a boxplot using seaborn with specified parameters
    sns.boxplot(
        data=dataframe,
        x=ranking_variable, # Set the x-axis variable based on rankings
        y=y_variable, # Set the y-axis variable
        hue=hue_variable, # Set color grouping based on the hue variable
        order=sorted(dataframe[y_variable].unique()), # Sort the y variable categories
        saturation=0.7, # Set color saturation
        linewidth=0.75, # Set box line width
        fliersize=3, # Size of the outlier markers
        ax=ax, # Specify the axis to plot on
    )

    # Hide the right and top spines for cleaner appearance
    ax.spines[["right", "top"]].set_visible(False)

    # Adjust the size of the tick labels on both axes
    ax.tick_params(axis="both", labelsize=9)
    ax.tick_params(axis="x", rotation=0) # Keep x-axis labels horizontal

     # Adjust legend position based on plot height
    if height > 5:
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left") # Legend outside the plot
    else:
        ax.legend(bbox_to_anchor=(0.5, -0.15), loc="upper center", ncol=2) # Legend centered below plot

    # Enable grid on the y-axis for better visibility of values
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)

    # Set margins for the y-axis
    plt.margins(y=0.02)

    # Close the figure to prevent it from displaying, then encode the figure in base64
    plt.close(fig)
    return get_base64_encoded_image(fig)  # Return base64-encoded image of the figure


def boxplots_mitigation_strategies_pretty(
    ER_Old, ER_Mitigation, Method, sampling_attribute=None, n_runs=1
):
    """Generate a boxplot comparing the old results with various mitigation strategies.
    
    Args:
        ER_Old: A dictionary or similar structure containing old exposure results for comparison.
        ER_Mitigation: A dictionary containing mitigation strategies and their corresponding exposure results.
        Method: A string indicating which mitigation strategy to visualize (e.g., 'Statistical_parity', 'Equal_parity').
        sampling_attribute: Optional. If provided, it will be used to categorize the boxplots on the x-axis.
        n_runs: Optional. The number of runs for sampling when `sampling_attribute` is provided.

    Returns:
        A base64 encoded string of the generated figure for use in web applications or reports.
    """

    # Set plot aesthetics
    plt.rcParams["mathtext.fontset"] = "dejavusans" # Use DejaVu Sans font for text
    plt.rcParams["figure.autolayout"] = True # Automatically adjust subplot parameters such that the subplot(s) fits in to the figure area

    width = 0.6 # Set the width for the boxplot
    font_size_out = 14 # Set the font size for output text

    # Create a figure and axes object for plotting
    fig, axes = plt.subplots(figsize=(10, 7), constrained_layout=True)

    # Define color mappings for boxplots based on methods
    Colors_boxplots = {"Statistical_parity": "darkblue", "Equal_parity": "gold"}

    # Properties for the boxplot elements (boxes, medians, whiskers, caps)
    PROPS = {
        "boxprops": {"facecolor": "none", "edgecolor": Colors_boxplots[Method]},
        "medianprops": {"color": Colors_boxplots[Method]},
        "whiskerprops": {"color": Colors_boxplots[Method]},
        "capprops": {"color": Colors_boxplots[Method]},
    }

    # Creating the DataFrame for mitigation strategies without sampling attribute
    if sampling_attribute == None:
        ER_Mitigation_DF = pd.DataFrame(ER_Mitigation.values(), columns=["ER_run"])
        sns.boxplot(
            data=ER_Mitigation_DF,
            y="ER_run",
            color=Colors_boxplots[Method],
            saturation=0.3,
            linewidth=0.75,
            ax=axes,
            **PROPS,
        )
    else: # Creating the DataFrame with the sampling attribute
        ER_Mitigation_DF = pd.DataFrame(
            {
                sampling_attribute: [
                    c for c in ER_Mitigation.keys() for n in range(n_runs)
                ],
                "ER_run": [n for c in ER_Mitigation.values() for n in c.values()],
            }
        )
        sns.boxplot(
            data=ER_Mitigation_DF,
            x=sampling_attribute,
            y="ER_run",
            color=Colors_boxplots[Method],
            saturation=0.3,
            linewidth=0.75,
            ax=axes,
            **PROPS,
        )

    # Add scatter plots for old exposure results
    if sampling_attribute == None:
        plt.scatter(0, ER_Old, color="purple", s=60, alpha=0.7) # Plot point for old exposure result
    else:
        plt.scatter(
            range(len(ER_Old)), list(ER_Old.values()), color="purple", s=60, alpha=0.7
        ) # Scatter points for each old result

     # Style the axes by hiding specific spines
    for spine in ["right", "top"]:
        axes.spines[spine].set_visible(False)

    # Adjust tick parameters for x-axis and y-axis
    axes.tick_params(
        "x", size=5, colors="black", labelsize=11, rotation=45
    )  # Customize appearance of x-axis ticks
    axes.tick_params("y", size=2, colors="black", labelsize=11)

    # Label axes with descriptions
    axes.set_ylabel(
        "Exposure distance women\nposition vs men position", size=12, labelpad=10
    )
    axes.set_xlabel(" ", size=0) # Keep x-axis label empty

    # Add horizontal dashed lines at specific y-ticks for better readability
    y_ticks = [float(str(i).split(", ")[1]) for i in axes.get_yticklabels()][2:-1]
    for l in y_ticks:
        if sampling_attribute == None:
            axes.hlines(l, -0.5, 0.5, "darkgrey", lw=1, ls="--")
        else:
            axes.hlines(l, -0.5, len(ER_Old) - 0.5, "darkgrey", lw=1, ls="--")

    # Adjust margins to prevent cutoff of the plot elements
    plt.margins(y=0.1)

    # Close the figure and encode it to base64 format for output
    plt.close(fig)
    enc_str = get_base64_encoded_image(fig)
    return enc_str

def get_base64_encoded_image(fig):
    """
    Generate a base64 encoded string from a matplotlib figure.
    
    Parameters:
    fig (matplotlib.figure.Figure): The matplotlib figure object to be converted.

    Returns:
    str: A base64 encoded string representation of the figure in PNG format.
    
    This function captures the current state of the provided matplotlib figure,
    saves it to a bytes buffer in PNG format, and then encodes that buffer 
    into a base64 string for easy embedding in HTML or other formats.
    
    Note:
    This function automatically closes the buffer after encoding to free up resources.
    """
    
    # Create an in-memory bytes buffer to hold the image data
    buffer = BytesIO()

    # Save the figure as a PNG image to the bytes buffer
    fig.savefig(buffer, format="png")

    # Move the buffer cursor to the beginning
    buffer.seek(0)

    # Read the buffer, encode the image to base64, and decode to a UTF-8 string
    img_str = base64.b64encode(buffer.read()).decode("utf-8")

    # Close the bytes buffer
    buffer.close()

    # Return the base64 encoded image string
    return img_str


def image_to_base64(image_path):
    """
    Convert an image file to a base64 encoded string.

    Args:
        image_path (str): The file path of the image to be converted.

    Returns:
        str: A base64 encoded string representation of the image.
        
    Raises:
        FileNotFoundError: If the specified image file does not exist.
        IOError: If there is an error reading the image file.
    """

    # Open the image file in binary read mode
    with open(image_path, "rb") as image_file:
        # Read the contents of the image file
        # and encode it using base64
        return base64.b64encode(image_file.read()).decode()


def generate_group_metrics_rows(ER_Old, ER_Mitigation, n_runs):
     """
    Generate HTML table rows containing metrics for groups based on old rankings and mitigation values.

    Args:
        ER_Old (dict): A dictionary containing old fairness values for each group. 
                       Each key represents a group, and the value is the old fairness metric.
        ER_Mitigation (dict): A dictionary containing lists of mitigation values for each group.
                              Each key represents a group, and the value is a list 
                              of fairness metrics from multiple runs.
        n_runs (int): The number of runs, which is the length of mitigation values for each group.

    Returns:
        str: A string containing HTML table row elements for each group with their respective metrics.
    """
    
    rows = [] # Initialize an empty list to hold the generated HTML rows

    for group in ER_Old.keys():
        # Extract the mitigation values for the current group across all runs
        mitigation_values = [ER_Mitigation[group][r] for r in range(n_runs)]

        # Calculate the mean fairness value for the group
        mean_fair = sum(mitigation_values) / len(mitigation_values)

        # Calculate the standard deviation of the mitigation values; if only one value, return 0
        std_fair = (
            statistics.stdev(mitigation_values) if len(mitigation_values) > 1 else 0
        )

        # Create an HTML table row for the current group including the metrics
        row = f"""
        <tr>
            <td>{group}</td>
            <td>{ER_Old[group]:.2f}</td>
            <td>{mean_fair:.2f}</td>
            <td>{std_fair:.2f}</td>
        </tr>
        """
        rows.append(row) # Append the generated row to the list of rows
        
    return "\n".join(rows) # Join all rows into a single string and return


def generate_group_stats(dataset, sampling_attribute):
     """
    Generate a summary of researcher counts for each unique value in a specified attribute of the dataset.

    Args:
        dataset (DataFrame): A pandas DataFrame containing at least one column corresponding to the sampling attribute.
        sampling_attribute (str): The name of the column in the dataset to group by and count researchers.

    Returns:
        str: A formatted string containing HTML paragraph elements with counts of researchers for each unique value
              in the specified sampling attribute, excluding NaN values.
    """
    # Initialize an empty list to store the formatted statistics for each group
    stats = []

    # Extract unique values of the specified attribute, excluding NaN values
    unique_values = [x for x in dataset[sampling_attribute].unique() if pd.notna(x)]

    # Sort the unique values to ensure consistent ordering
    for group in sorted(unique_values):
        # Count the number of researchers in the dataset belonging to the current group
        count = len(dataset[dataset[sampling_attribute] == group])

        # Append a formatted string with the group name and count to the stats list
        stats.append(f"<p>{group}: {count} researchers</p>")

    # Join all formatted strings into a single string and return it
    return "\n".join(stats)


template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            color: #333;
        }}
        .csh-container {{
            display: grid;
            grid-template-columns: 250px 1fr 300px;
            gap: 20px;
        }}
        .parameters, .dataset-info {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
        }}
        .main-content {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .metrics-table th, .metrics-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .visualization {{
            margin: 20px 0;
            text-align: center;
        }}
        .figure-caption {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            font-size: 0.9em;
        }}
        .caption-definition {{
            margin-bottom: 10px;
            font-style: italic;
        }}
        .caption-elements {{
            margin-top: 10px;
        }}
        .caption-element {{
            margin: 5px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .element-marker {{
            width: 20px;
            height: 20px;
            display: inline-block;
        }}
        .dot-marker {{
            background: purple;
            border-radius: 50%;
        }}
        .boxplot-marker {{
            background: #4682b4;
        }}
        .visualization-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .visualization-full {{
            grid-column: 1 / -1;
        }}
        .visualization-half {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }}
        .visualization-half img {{
            max-height: 300px;
            width: auto;
            object-fit: contain;
            margin: auto;
        }}
        .network-visualization img {{
            max-width: 500px;
            display: block;
            margin: auto;
        }}
        .exposure-distance-visualization img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 70%;
        }}
        .network-stats {{
            font-size: 0.9em;
            margin: 10px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}
        .network-stat {{
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
        }}
        .section-title {{
            margin: 20px 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid #007bff;
            color: #2c3e50;
        }}
        .hidden {{
            display: none;
        }}
    </style>
    <script>
        function toggleProtectedAttribute() {{
            var selectedValue = document.getElementById("protected-attribute").value;
            document.getElementById("female-section").classList.add("hidden");
            document.getElementById("male-section").classList.add("hidden");
            document.getElementById(selectedValue + "-section").classList.remove("hidden");
        }}
    </script>
</head>
<body>
    <div class="csh-container">
        <div class="parameters">
            <h3>Initial parameters</h3>
            <div class="protected-attributes">
                <h4>Protected attributes:</h4>
                <div>Sensitive attribute: {sensitive_attribute}</div>
                <div class="dropdown-container">
                    <label for="protected-attribute">Select Protected Attribute:</label>
                    <select id="protected-attribute" onchange="toggleProtectedAttribute()">
                        <option value="female">Female</option>
                        <option value="male">Male</option>
                    </select>
                </div>
                <div>Sampling attribute: {sampling_attribute}</div>
            </div>
            <div class="ranking-metrics">
                <h4>Ranking variable:</h4>
                <div>{ranking_variable}</div>
            </div>
        </div>

        <div class="main-content">
            <div id="female-section" class="female-protected">
                {female_fragment}
            </div>
            <div id="male-section" class="male-protected hidden">
                {male_fragment}
            </div>

        </div>

        <div class="dataset-info">
            <h3>Analysis Information</h3>
            <p><strong>Number of runs:</strong> {n_runs}</p>
            <p><strong>Method:</strong> Statistical Parity</p>
            
            <h4>Group Statistics:</h4>
            {group_stats}
        </div>
    </div>
</body>
</html>
"""

protected_fragment = """
    <div class="visualization-full network-visualization">
        <h3 class="section-title">1. Network Structure</h3>
        <img src="data:image/png;base64,{network_img_str}" alt="Network" style="width: 100%;"/>
        <div class="network-stats">
            <div class="network-stat">Nodes: 1739</div>
            <div class="network-stat">Edges: 9943</div>
            <div class="network-stat">Density: 0.003</div>
            <div class="network-stat">LCC: 0.65</div>
            <div class="network-stat">CC: 529</div>
        </div>
    </div>
    
    <div class="visualization-full">
        <h3 class="section-title">2. Categorical Distribution</h3>
        <img src="data:image/png;base64,{normal_distribution_img_str}" alt="Categorical Distribution" style="width: 100%;"/>
        <div class="figure-caption">
            Distribution of {ranking_variable} across categories, separated by gender.
        </div>
        <img src="data:image/png;base64,{distribution_img_str}" alt="Categorical Distribution" style="width: 100%;"/>
        <div class="figure-caption">
            Post-Mitigation Distribution of {ranking_variable} across categories, separated by gender.
        </div>
    </div>

    <h3 class="section-title">3. Exposure Distance Analysis</h3>
    <div class="visualization-full exposure-distance-visualization">
        <img src="data:image/png;base64,{er_viz_str}" alt="Exposure Distance Visualization" />
        <div class="figure-caption">
            <div class="caption-definition">
                The Exposure Distance (ED) measures how fair is the visibility of researchers from different demographic groups in rankings. 
                In this plot, we compare the position of each woman vs. each man inside the income group categories, and then we average those values. 
                A value of ED closer to 0 means a fairer representation, and we show how using a mitigation strategy (statistical parity in this case) 
                improves the metric, making it smaller.
            </div>
            <div class="caption-elements">
                <div class="caption-element">
                    <span class="element-marker dot-marker"></span>
                    Purple dots show the Exposure Distance when researchers are ranked by raw degree centrality
                </div>
                <div class="caption-element">
                    <span class="element-marker boxplot-marker"></span>
                    Box plots show the distribution of Exposure Distance across {n_runs} runs of the fairness-aware ranking algorithm
                </div>
            </div>
        </div>
    </div>

    <div class="metrics">
        <h3>Results</h3>
        
        <h4>Exposure Distance by Group</h4>
        <table class="metrics-table">
            <tr>
                <th>Group</th>
                <th>Original ED</th>
                <th>Mean Fair ED</th>
                <th>Std Dev Fair ED</th>
            </tr>
            {group_metrics_rows}
        </table>

        <h4>Statistical Summary</h4>
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Original</th>
                <th>Fair (Mean)</th>
            </tr>
            <tr>
                <td>Max ED Disparity</td>
                <td>{max_disparity_old:.2f}</td>
                <td>{max_disparity_new:.2f}</td>
            </tr>
            <tr>
                <td>Std Dev Across Groups</td>
                <td>{std_dev_old:.2f}</td>
                <td>{std_dev_new:.2f}</td>
            </tr>
        </table>
    </div>
"""


def generate_html_fragment(
    ranking_variable,
    ER_Old,
    ER_Mitigation,
    boxplot_img_str,
    network_img_str,
    normal_distribution_img_str,
    distribution_img_str,
    n_runs,
):
     """
    Generates an HTML fragment displaying statistical visualizations and metrics.

    Args:
        ranking_variable (str): The variable used for ranking groups in the analysis.
        ER_Old (dict): A dictionary containing old equity ratio values for different groups.
        ER_Mitigation (dict): A dictionary containing mitigation equity ratio values for different groups for several runs.
        boxplot_img_str (str): HTML string representation of the boxplot image.
        network_img_str (str): HTML string representation of the network image.
        normal_distribution_img_str (str): HTML string representation of the normal distribution image.
        distribution_img_str (str): HTML string representation of the overall distribution image.
        n_runs (int): The number of simulation runs used for calculating averages.

    Returns:
        str: An HTML fragment containing the visualizations and statistical summaries.
    """
    
    # Calculate the maximum disparity in the old equity ratios by subtracting min from max
    max_disparity_old = max(ER_Old.values()) - min(ER_Old.values())

    # Calculate the mean mitigation equity ratio for each group over the specified runs
    mean_mitigation_by_group = {
        group: statistics.mean([ER_Mitigation[group][r] for r in range(n_runs)])
        for group in ER_Old.keys()
    }

    # Calculate the maximum disparity in the new (mean mitigation) rankings
    max_disparity_new = max(mean_mitigation_by_group.values()) - min(
        mean_mitigation_by_group.values()
    )

    # Prepare the HTML content by inserting the calculated values and images into the template
    html_content = protected_fragment.format(
        er_viz_str=boxplot_img_str, # Boxplot image string
        network_img_str=network_img_str,  # Network visualization image string
        ranking_variable=ranking_variable, # Ranking variable used
        normal_distribution_img_str=normal_distribution_img_str, # Normal distribution image string
        distribution_img_str=distribution_img_str, # Overall distribution image string
        group_metrics_rows=generate_group_metrics_rows(ER_Old, ER_Mitigation, n_runs), # Generate metrics row for groups
        max_disparity_old=max_disparity_old, # Max disparity in old rankings
        max_disparity_new=max_disparity_new,  # Max disparity in new rankings
        std_dev_old=statistics.stdev(list(ER_Old.values())), # Standard deviation of old rankings
        std_dev_new=statistics.stdev(list(mean_mitigation_by_group.values())),  # Standard deviation of new rankings
        n_runs=n_runs, # Number of simulation runs
    )

    return html_content # Return the generated HTML content


def generate_html_report(
    dataset,
    sensitive_attribute,
    sampling_attribute,
    ranking_variable,
    female_fragment,
    male_fragment,
    n_runs,
):
    """
    Generates an HTML report based on the provided dataset and specified attributes.

    Args:
        dataset (pd.DataFrame): The dataset containing the data to be analyzed.
        sensitive_attribute (str): The sensitive attribute to be reported on (e.g. gender, race).
        sampling_attribute (str): The attribute used for sampling in the analysis.
        ranking_variable (str): The variable used for ranking groups in the report.
        female_fragment (str): HTML fragment to represent female group in the report.
        male_fragment (str): HTML fragment to represent male group in the report.
        n_runs (int): The number of runs for which the report is being generated.

    Returns:
        HTML: An HTML object containing the generated report.
    """

     # Generate the HTML content by formatting the template with provided arguments
    html_content = template.format(
        sensitive_attribute=sensitive_attribute,
        sampling_attribute=sampling_attribute,
        ranking_variable=ranking_variable,
        group_stats=generate_group_stats(dataset, sampling_attribute),
        female_fragment=female_fragment,
        male_fragment=male_fragment,
        n_runs=n_runs,
    )
    return HTML(html_content)  # Return the generated HTML content as an HTML object


def plot_network(
    G,
    title,
    name_plot,
    directed=False,
    amplyfing_size_nodes=2,
    division_size_edges=100,
    size_edges=1,
):
    """
    Plots a network graph using NetworkX and visualizes it with Matplotlib.

    Parameters:
    G (networkx.Graph): The graph to be plotted. Can be a directed or undirected graph.
    title (str): The title of the plot to be displayed.
    name_plot (str): The name to be used for saving the plot (this does not affect the current implementation).
    directed (bool): Indicates if the graph is directed. Default is False (undirected).
    amplyfing_size_nodes (int): Factor to amplify the node sizes based on their degree. Default is 2.
    division_size_edges (int): Value used to normalize edge weights for visualization. Default is 100.
    size_edges (int): Base size of edges. Default is 1.
    
    Returns:
    str: A base64 encoded string representation of the plot image.
    """
    
    # Get the degree of each node in the graph as a dictionary
    degree = dict(G.degree(weight="weight"))

    # Retrieve weights for each edge based on their attributes
    weights = [G[u][v]["weight"] for u, v in G.edges()]

    # Compute node positions using the ForceAtlas2 layout algorithm
    pos = networks_layouts.forceatlas2_layout(
        G,
        max_iter=300,
        jitter_tolerance=0.2,
        scaling_ratio=10,
        gravity=0.05,
        distributed_action=False,
        strong_gravity=True,
        node_mass=[400 for i in list(degree.values())],
        node_size=[400 for i in list(degree.values())],
        weight=weights,
        dissuade_hubs=True,
        linlog=False,
        seed=10,
        dim=2,
    )

    # Create a figure for the plot
    ncols = 1 # Number of columns
    nrows = 1 # Number of rows

    # Generate the subplots
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=(10, 10))

    # Draw the network graph
    nx.draw_networkx(
        G,
        with_labels=False, # No labels on the nodes
        pos=pos, # Node positions
        node_color=(255 / 256, 102 / 256, 102 / 256, 0.7), # Node color with transparency
        node_size=[i * amplyfing_size_nodes + 1 for i in list(degree.values())], # Adjust node sizes
        edge_color="lightgray", # Edge color
        width=np.array(weights) / division_size_edges + size_edges, # Determine edge width based on weights
        arrowsize=3, # Size of arrows if the graph is directed
        ax=axes, # Axes to plot on
    )

    # Determine connected components based on directed/undirected
    if directed == False:
        Connected_componets = sorted(nx.connected_components(G), key=len, reverse=True)
    else:
        Connected_componets = sorted(
            nx.weakly_connected_components(G), key=len, reverse=True
        )

    # Set the title of the plot
    plt.title(title, fontweight="bold", fontsize=20)

    # Remove the spines (borders) from the plot
    for axis in ["top", "bottom", "left", "right"]:
        axes.spines[axis].set_linewidth(0)

    # Save the figure and close it to free up memory
    plt.close(fig)

     # Encode the plot in base64 to facilitate embedding in other formats (like HTML)
    enc_str = get_base64_encoded_image(fig)
    
    return enc_str


@metric(namespace="mammotheu", version="v0037", python="3.11")
def exposure_distance_comparison(
    dataset: Graph_CSH,
    model: ResearcherRanking,
    sensitive: List[str] = "Gender",
    n_runs: int = 1,
    sampling_attribute: str = "Nationality_IncomeGroup",
    ranking_variable: mammoth.integration.Options(
        "Degree", "Citations", "Productivity"
    ) = "Degree",
) -> HTML:
    """
   Compute the exposure distance between the protected and non-protected groups in the dataset and ranking.

    Sensitive attributes is a comma-separated list of the attributes relevant for fairness analysis. Currently,
    only *Gender* is supported.
    
    Args:
        dataset (Graph_CSH): The dataset containing researcher information and their connections.
        model (ResearcherRanking): A model used for ranking researchers based on specified criteria.
        sensitive (List[str]): A list of sensitive attributes relevant for fairness analysis (default is ["Gender"]).
        n_runs (int): Number of runs for ranking; choose a natural number between 1 and 100 (default is 1).
        sampling_attribute (str): The attribute used for grouping analysis; options are *Nationality_IncomeGroup* or *Nationality_Region* (default is "Nationality_IncomeGroup").
        ranking_variable (mammoth.integration.Options): The main criteria for ranking researchers; options include *Degree*, *Citations*, or *Productivity* (default is "Degree").
    
    Returns:
        HTML: An HTML report detailing the exposure distances and visualizations for protected and non-protected groups.
    """

    fragments = {"male": "", "female": ""}
    for protected in ["female", "male"]:
        n_runs = int(n_runs)

       # Initialize the baseline model for ranking
        model_baseline = model.baseline_rank

        # Extract the researchers' graph from the dataset
        researchers_graph = dataset.G

        # Plot the network if the number of nodes is less than 2500
        if len(researchers_graph.nodes) < 2500:
            network_image = plot_network(
                G=researchers_graph,
                title=" Co-authorship network",
                name_plot="Co-authorship_network.pdf",
            )
        else:
            # Convert large network image to a base64 string instead
            network_image = image_to_base64("./data/researchers/network.png")

        # Prepare nodes for DataFrame creation
        Dataframe_nodes = {"id": []}
        for i in researchers_graph.nodes():
            Dataframe_nodes["id"] += [i]
            # Populate other attributes of nodes
            for k, v in researchers_graph.nodes[i].items():
                try:
                    Dataframe_nodes[k] += [v]
                except:
                    # Initialize the key in the dictionary if it doesn't exist.
                    Dataframe_nodes[k] = [v]

        # Convert the node data into a pandas DataFrame.
        data = pd.DataFrame(Dataframe_nodes)

        # Only include rows where the sampling attribute is not missing.
        dataframe_sampling = data[~data[sampling_attribute].isnull()]

        # Store the original ranking variable and the sensitive and protected attributes.
        Old_ranking_variable = ranking_variable
        sensitive_attribute = sensitive[0]
        protected_attribute = protected

        ER_Old = {} # To store exposure distances under old ranking.
        ER_Mitigation = {} # To store exposure distances under mitigation strategies.

        ranked_dataframe_normal = pd.DataFrame() # DataFrame for normal ranking results.
        ranked_dataframe_mitigation = pd.DataFrame() # DataFrame for mitigation ranking results.

        # Iterate over each category defined by the sampling attribute.
        for category in sorted(set(dataframe_sampling[sampling_attribute])):

            # Filter the main DataFrame for the current category.
            dataframe_filtered = dataframe_sampling[
                dataframe_sampling[sampling_attribute] == category
            ]

            print(f"{len(dataframe_filtered)} researchers in the category {category}")

            # Rank the filtered DataFrame using the baseline model.
            if callable(model_baseline):
                ranked_dataframe_normal_category = model_baseline(
                    dataframe_filtered, ranking_variable
                )
            else:
                ranked_dataframe_normal_category = model_baseline.rank(
                    dataframe_filtered, ranking_variable
                )

            # Compute the exposure distance for the baseline ranking.
            ER_Old[category] = Exposure_distance(
                ranked_dataframe_normal_category,
                ranking_variable=Old_ranking_variable,
                sensitive_attribute=sensitive_attribute,
                protected_attirbute=protected_attribute,
            )

            
            ranked_dataframe_normal = pd.concat(
                [ranked_dataframe_normal, ranked_dataframe_normal_category]
            )

            # Compute exposure distance for mitigation strategies
            ER_Mitigation[category] = {}
            ranked_dataframe_mitigation_category_runs = []

            for r in range(n_runs):
                # Rank the rows using the model
                if callable(model):
                    ranked_dataframe_mitigation_category = model(
                        dataframe_filtered, ranking_variable
                    )
                else:
                    ranked_dataframe_mitigation_category = model.rank(
                        dataframe_filtered, ranking_variable
                    )
                    
                # Calculate exposure distance for mitigation
                ER_Mitigation[category][r] = Exposure_distance(
                    ranked_dataframe_mitigation_category,
                    ranking_variable=Old_ranking_variable,
                    sensitive_attribute=sensitive_attribute,
                    protected_attirbute=protected_attribute,
                )
                ranked_dataframe_mitigation_category_runs.append(
                    ranked_dataframe_mitigation_category
                )

            # Concatenate all runs to create a single DataFrame
            all_runs_df = pd.concat(ranked_dataframe_mitigation_category_runs)

            # Separate numeric columns for computing mean rankings
            numeric_cols = all_runs_df.select_dtypes(include=[np.number]).columns
            mean_ranking_df = all_runs_df[numeric_cols].groupby(level=0).mean()

            # For non-numeric columns, take the first occurrence
            non_numeric_df = (
                all_runs_df.select_dtypes(exclude=[np.number]).groupby(level=0).first()
            )

            # Merge numeric and non-numeric DataFrames
            mean_ranking_df = pd.concat([mean_ranking_df, non_numeric_df], axis=1)

            ## Append the mean ranking DataFrame to the main mitigation DataFrame
            ranked_dataframe_mitigation = pd.concat(
                [ranked_dataframe_mitigation, mean_ranking_df]
            )

        # Generate boxplots for normal ranking distribution
        normal_distribution_image = boxplots_rankings(
            ranked_dataframe_normal,
            hue_variable=sensitive_attribute,
            y_variable=sampling_attribute,
            ranking_variable="Ranking_" + Old_ranking_variable,
        )

        # Generate boxplots for the mitigated ranking distribution
        distribution_image = boxplots_rankings(
            ranked_dataframe_mitigation,
            hue_variable=sensitive_attribute,
            y_variable=sampling_attribute,
            ranking_variable="Ranking_" + Old_ranking_variable,
        )

        # Generate images for different mitigation strategies
        mitigation_strategies_image = boxplots_mitigation_strategies_pretty(
            ER_Old,
            ER_Mitigation,
            Method="Statistical_parity",
            sampling_attribute=sampling_attribute,
            n_runs=n_runs,
        )

        # Create HTML fragments for each protected group
        fragments[protected] = generate_html_fragment(
            ranking_variable=ranking_variable,
            ER_Old=ER_Old,
            ER_Mitigation=ER_Mitigation,
            boxplot_img_str=mitigation_strategies_image,
            network_img_str=network_image,
            normal_distribution_img_str=normal_distribution_image,
            distribution_img_str=distribution_image,
            n_runs=n_runs,
        )

    # Generate the full HTML report from the collected fragments
    return generate_html_report(
        dataset=data,
        sensitive_attribute=sensitive,
        sampling_attribute=sampling_attribute,
        ranking_variable=ranking_variable,
        female_fragment=fragments["female"],
        male_fragment=fragments["male"],
        n_runs=n_runs,
    )
