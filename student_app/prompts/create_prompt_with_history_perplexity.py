from typing import List, Dict


def reformat_prompt(prompt: str, **kwargs) -> str:
    try:
        return prompt.format(**kwargs)
    except KeyError as e:
        missing_key = str(e).strip("'")
        raise ValueError(f"Missing required placeholder: {missing_key}")


def set_prompt_with_history(system_prompt: str, chat_history: List[Dict[str, str]], user_prompt: str) -> List[Dict[str, str]]:

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        *chat_history,
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    print(messages)
    return messages