# backend/assistant/tools/filter_tool/data_loader.py

import pandas as pd
from api_assistant.config import Config

def load_course_data(csv_path='your_course_data.csv'):
    """
    Loads course data from a CSV file into a pandas DataFrame.

    Args:
        csv_path (str): Path to the CSV file containing course data.

    Returns:
        pd.DataFrame: DataFrame containing course information.
    """
    df = pd.read_csv(csv_path)
    # Perform any necessary preprocessing here
    return df

# Example usage
# df_expanded = load_course_data()
