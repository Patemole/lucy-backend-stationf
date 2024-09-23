# backend/assistant/tools/filter_tool/filter_manager.py

import json
from .filters import (
    filter_exact_match,
    filter_contains,
    filter_exclude_values,
    filter_numeric_comparison,
    filter_schedule_and_location,
    filter_prerequisites,
)
from .data_loader import load_course_data

# Mapping of filters to handlers
FILTER_HANDLERS = {
    "name": {
        "handler": filter_contains,
        "type": "partial"  # Partial matching (contains)
    },
    "code": {
        "handler": filter_exact_match,
        "type": "exact"  # Exact matching
    },
    "Schedule Type": {
        "handler": filter_exact_match,
        "type": "exact"  # Exact matching
    },
    "Instruction Method": {
        "handler": filter_exact_match,
        "type": "exact"  # Exact matching
    },
    "Credit": {
        "handler": filter_numeric_comparison,
        "type": "comparison"  # Numeric comparison
    },
    "Course Description": {
        "handler": filter_contains,
        "type": "partial"  # Partial matching
    },
    "Section Details": {
        "handler": filter_contains,
        "type": "partial"  # Partial matching
    },
    "Registration Restrictions": {
        "handler": filter_contains,
        "type": "partial"  # Partial matching
    },
    "Section Attributes": {
        "handler": filter_exact_match,
        "type": "exact"  # Exact matching
    },
    "Schedule and Location": {
        "handler": filter_schedule_and_location,
        "type": "complex"  # Complex filtering
    },
    "Instructors": {
        "handler": filter_contains,
        "type": "partial"  # Partial matching
    },
    "Course Quality": {
        "handler": filter_numeric_comparison,
        "type": "comparison"  # Numeric comparison
    },
    "Instructor Quality": {
        "handler": filter_numeric_comparison,
        "type": "comparison"  # Numeric comparison
    },
    "Work Required": {
        "handler": filter_numeric_comparison,
        "type": "comparison"  # Numeric comparison
    },
    "Difficulty": {
        "handler": filter_numeric_comparison,
        "type": "comparison"  # Numeric comparison
    },
    "Prerequisites": {
        "handler": filter_prerequisites,
        "type": "exact"  # Exact matching
    },
    # Add more mappings as needed
}


def apply_filters(filters, csv_path='.combined_courses_final.csv'):
    """
    Loads the course data, applies the provided filters, and returns the filtered data as JSON.

    Parameters:
    - filters (dict): Dictionary containing filter criteria.
    - csv_path (str): Path to the CSV file containing course data.

    Returns:
    - str: JSON string of the filtered DataFrame.
    """
    print("Loading course data...")
    df = load_course_data(csv_path)
    print("Course data loaded successfully.\n")

    print("Applying filters to the DataFrame...")
    df_filtered = df.copy()

    for key, value in filters.items():
        print(f"Processing filter: {key} = {value}")

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
                # Assuming 'value' is a list of conditions like ['>= 4', '<= 5']
                for condition in value:
                    df_filtered = handler(df_filtered, key, condition)
            elif filter_type == "complex":
                df_filtered = handler(df_filtered, value)
            else:
                print(f"Unsupported filter type '{filter_type}' for key '{key}'. Skipping.")
        else:
            print(f"Warning: No handler defined for key '{key}'. Skipping.")

    print("Filtering complete.\n")

    if df_filtered.empty:
        print("No courses match your query.\n")
        return json.dumps([])  # Return empty JSON array
    else:
        print("Filtered DataFrame:")
        #print(df_filtered.to_string(index=False))  # Optional: can remove for simplicity
        print()
        return df_filtered.to_json(orient='records')  # Return JSON array
