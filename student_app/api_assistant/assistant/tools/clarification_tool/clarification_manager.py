def get_clarifying_question_output(arguments):
    question = arguments.get('question', '')
    answer_options = arguments.get('answer_options', [])
    tool_output = [{
        "document_id": "4",
        "question": question,
        "answer_options": answer_options,
        "other_specification": {
            "label": "If other, please specify",
            "placeholder": "e.g., None"
        }
    }]
    return tool_output
