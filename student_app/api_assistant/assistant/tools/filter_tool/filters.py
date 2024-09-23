# backend/assistant/tools/filter_tool/filters.py

import re
import json
import pandas as pd
from datetime import datetime

def filter_exact_match(df, column, values):
    """Filter rows where the column value exactly matches any of the provided values."""
    if df[column].dtype == object:
        # Case-insensitive exact match for strings
        return df[df[column].str.lower().isin([v.lower() for v in values])]
    else:
        # Exact match for non-strings
        return df[df[column].isin(values)]

def filter_contains(df, column, values):
    """Filter rows where the column value contains any of the provided substring values."""
    mask = df[column].astype(str).str.lower().str.contains('|'.join([v.lower() for v in values]))
    return df[mask]

def filter_exclude_values(df, column, values):
    """
    Filter out rows where the column value contains any of the provided exclude values.

    Parameters:
    - df (pd.DataFrame): The DataFrame to filter.
    - column (str): The column name to apply the filter on.
    - values (list of str): A list of substring values to exclude.

    Returns:
    - pd.DataFrame: The filtered DataFrame.
    """
    if df[column].dtype == object:
        pattern = '|'.join([re.escape(v) for v in values])
        mask = ~df[column].str.contains(pattern, case=False, regex=True, na=False)
        return df[mask]
    else:
        return df[~df[column].isin(values)]

def filter_numeric_comparison(df, column, condition):
    """Filter rows based on a numeric comparison condition (e.g., '> 4')."""
    match = re.match(r"([<>=]+)\s*(\d+(\.\d+)?)", condition)
    if not match:
        print(f"Invalid condition format for {column}: {condition}")
        return df
    operator, value, _ = match.groups()
    value = float(value)

    if operator == ">=":
        return df[df[column] >= value]
    elif operator == "<=":
        return df[df[column] <= value]
    elif operator == ">":
        return df[df[column] > value]
    elif operator == "<":
        return df[df[column] < value]
    elif operator == "==":
        return df[df[column] == value]
    else:
        print(f"Unsupported operator '{operator}' for {column}")
        return df

def parse_schedule(schedule_str):
    """
    Parses the schedule string to extract days and time ranges.
    Handles multiple days and time ranges in a single string.
    Example input: 'MW 3:30pm-4:59pm, R 10:10am-11:00am'

    Returns:
    - schedule_info: A list of tuples, each containing:
        (days: list of days, start_time: datetime.time, end_time: datetime.time)
    """
    schedule_parts = schedule_str.split(',')

    schedule_info = []
    time_pattern = re.compile(r"([MTWRF]+)\s(\d{1,2}:\d{2}(?:am|pm))-(\d{1,2}:\d{2}(?:am|pm))")

    for part in schedule_parts:
        match = time_pattern.search(part.strip())
        if match:
            days_str = match.group(1)  # E.g., 'MW'
            start_time_str = match.group(2)  # E.g., '3:30pm'
            end_time_str = match.group(3)  # E.g., '4:59pm'

            days = list(days_str)
            start_time = datetime.strptime(start_time_str, '%I:%M%p').time()
            end_time = datetime.strptime(end_time_str, '%I:%M%p').time()

            schedule_info.append((days, start_time, end_time))

    return schedule_info

def filter_schedule_and_location(df, schedule_filters):
    """
    Filters the DataFrame based on the schedule and location filters provided by the user.

    Parameters:
    - df: The DataFrame containing course information.
    - schedule_filters: A dictionary containing the following:
        - include_days (list): List of days to include (e.g., ['M', 'W']).
        - exclude_days (list): List of days to exclude (e.g., ['F']).
        - include_time_range (tuple): Start and end time as a tuple (e.g., ('8:00am', '12:00pm')).
        - exclude_time_range (tuple): Start and end time as a tuple to exclude (optional).

    Returns:
    - Filtered DataFrame based on the schedule and location filters.
    """
    include_days = schedule_filters.get('include_days', [])
    exclude_days = schedule_filters.get('exclude_days', [])
    include_time_range = schedule_filters.get('include_time_range', None)
    exclude_time_range = schedule_filters.get('exclude_time_range', None)

    if include_time_range:
        include_start_time = datetime.strptime(include_time_range[0], '%I:%M%p').time()
        include_end_time = datetime.strptime(include_time_range[1], '%I:%M%p').time()
    else:
        include_start_time = None
        include_end_time = None

    if exclude_time_range:
        exclude_start_time = datetime.strptime(exclude_time_range[0], '%I:%M%p').time()
        exclude_end_time = datetime.strptime(exclude_time_range[1], '%I:%M%p').time()
    else:
        exclude_start_time = None
        exclude_end_time = None

    def schedule_matches(schedule_str):
        schedule_info = parse_schedule(schedule_str)

        for days, start_time, end_time in schedule_info:
            if include_days and not any(day in days for day in include_days):
                continue
            if exclude_days and any(day in days for day in exclude_days):
                continue

            if include_start_time and include_end_time:
                if not (start_time >= include_start_time and end_time <= include_end_time):
                    continue

            if exclude_start_time and exclude_end_time:
                if start_time >= exclude_start_time and end_time <= exclude_end_time:
                    continue

            return True

        return False

    df_filtered = df[df['Schedule and Location'].apply(schedule_matches)]

    return df_filtered

def filter_prerequisites(df, prerequisites_filter):
    """
    Filters the DataFrame based on the prerequisites requirements.

    Parameters:
    - df: The DataFrame containing course information.
    - prerequisites_filter: A dictionary containing the following:
        - has_prerequisites (boolean): If True, include courses with prerequisites. If False, include courses with no prerequisites.
        - prerequisites_to_include (list): A list of specific prerequisites to include (e.g., 'CIS 1210').
        - prerequisites_to_exclude (list): A list of specific prerequisites to exclude (e.g., 'CIS 1210').

    Returns:
    - Filtered DataFrame based on the prerequisites filter.
    """
    has_prerequisites = prerequisites_filter.get('has_prerequisites', None)
    prerequisites_to_include = prerequisites_filter.get('prerequisites_to_include', [])
    prerequisites_to_exclude = prerequisites_filter.get('prerequisites_to_exclude', [])

    if has_prerequisites is False:
        df = df[df['Prerequisites'].isna()]

    if has_prerequisites is True:
        df = df[df['Prerequisites'].notna()]

    if prerequisites_to_include:
        df = df[df['Prerequisites'].apply(lambda prereqs: any(course in prereqs for course in prerequisites_to_include))]

    if prerequisites_to_exclude:
        df = df[df['Prerequisites'].apply(lambda prereqs: all(course not in prereqs for course in prerequisites_to_exclude))]

    return df
