# backend/assistant/tools/filter_tool/filter_manager.py

from .filters import (
    filter_exact_match,
    filter_contains,
    filter_exclude_values,
    filter_numeric_comparison,
    filter_numeric_list_match,
    filter_schedule_and_location,
    filter_prerequisites
)

FILTER_HANDLERS = {
    "name": {
        "handler": filter_contains,
        "type": "partial"
    },
    "code": {
        "handler": filter_contains,
        "type": "partial"
    },
    "Schedule Type": {
        "handler": filter_exact_match,
        "type": "exact"
    },
    "Instruction Method": {
        "handler": filter_exact_match,
        "type": "exact"
    },
    "Credit": {
        "handler": filter_numeric_list_match,
        "type": "exact_list"
    },
    "Course Description": {
        "handler": filter_contains,
        "type": "partial"
    },
    "Section Details": {
        "handler": filter_contains,
        "type": "partial"
    },
    "Registration Restrictions": {
        "handler": filter_contains,
        "type": "partial"
    },
    "Section Attributes": {
        "handler": filter_exact_match,
        "type": "exact"
    },
    "Schedule and Location": {
        "handler": filter_schedule_and_location,
        "type": "complex"
    },
    "Instructors": {
        "handler": filter_contains,
        "type": "partial"
    },
    "Course Quality": {
        "handler": filter_numeric_comparison,
        "type": "comparison"
    },
    "Instructor Quality": {
        "handler": filter_numeric_comparison,
        "type": "comparison"
    },
    "Work Required": {
        "handler": filter_numeric_comparison,
        "type": "comparison"
    },
    "Difficulty": {
        "handler": filter_numeric_comparison,
        "type": "comparison"
    },
    "Prerequisites": {
        "handler": filter_prerequisites,
        "type": "complex"
    },
    # Add more mappings as needed
}

def apply_filters(filters, df):
    df_filtered = df.copy()
    for key, value in filters.items():
        if key in FILTER_HANDLERS:
            handler_info = FILTER_HANDLERS[key]
            handler = handler_info["handler"]
            filter_type = handler_info["type"]
            if key == "Schedule and Location":
                df_filtered = handler(df_filtered, value)
            elif filter_type == "exact":
                df_filtered = handler(df_filtered, key, value)
            elif filter_type == "partial":
                df_filtered = handler(df_filtered, key, value)
            elif filter_type == "comparison":
                df_filtered = handler(df_filtered, key, value)
            elif filter_type == "complex":
                df_filtered = handler(df_filtered, value)
            elif filter_type == "exact_list":
                df_filtered = handler(df_filtered, key, value)
            else:
                continue
        else:
            continue
    return df_filtered
