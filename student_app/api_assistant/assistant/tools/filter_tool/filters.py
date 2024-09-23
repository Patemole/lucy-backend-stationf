# backend/assistant/tools/filter_tool/filters.py

import re
from datetime import datetime
import pandas as pd

def filter_exact_match(df, column, values):
    if df[column].dtype == object:
        return df[df[column].str.lower().isin([v.lower() for v in values])]
    else:
        return df[df[column].isin(values)]

def filter_contains(df, column, values):
    mask = df[column].astype(str).str.lower().str.contains('|'.join([v.lower() for v in values]))
    return df[mask]

def filter_exclude_values(df, column, values):
    if df[column].dtype == object:
        pattern = '|'.join([re.escape(v) for v in values])
        mask = ~df[column].str.contains(pattern, case=False, regex=True, na=False)
        return df[mask]
    else:
        return df[~df[column].isin(values)]

def filter_numeric_comparison(df, column, condition):
    condition = condition.strip()
    operators = [">=", "<=", "==", ">", "<"]
    for op in operators:
        if op in condition:
            value_str = condition.replace(op, "").strip()
            try:
                value = float(value_str)
            except ValueError:
                return df
            if op == ">=":
                return df[df[column] >= value]
            elif op == "<=":
                return df[df[column] <= value]
            elif op == ">":
                return df[df[column] > value]
            elif op == "<":
                return df[df[column] < value]
            elif op == "==":
                return df[df[column] == value]
    return df

def filter_numeric_list_match(df, column, values):
    filter_values = [float(v) for v in values]
    def has_common(x):
        if isinstance(x, list):
            return any(item in filter_values for item in x)
        return False
    return df[df[column].apply(has_common)]

def filter_schedule_and_location(df, schedule_filters):
    include_days = schedule_filters.get('include_days', [])
    exclude_days = schedule_filters.get('exclude_days', [])
    included_hours = schedule_filters.get('included_hours', [])
    excluded_hours = schedule_filters.get('excluded_hours', [])
    if include_days:
        df = filter_contains(df, 'Schedule and Location', include_days)
    if exclude_days:
        df = filter_exclude_values(df, 'Schedule and Location', exclude_days)
    if included_hours:
        df = filter_contains(df, 'Schedule and Location', included_hours)
    if excluded_hours:
        df = filter_exclude_values(df, 'Schedule and Location', excluded_hours)
    return df

def filter_prerequisites(df, prerequisites_filter):
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
