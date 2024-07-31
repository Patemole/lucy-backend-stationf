from typing import List, Dict

def pplx_messages_format_validation(messages: List[Dict[str, str]]) -> bool:

    # Check if the list of messages is a list
    if not isinstance(messages, list):
        print("The list of messages is not a list.")
        return False
    
    # check message one by one
    for message in messages:

        # Check if the list of messages is a list of dictionaries
        if not all(isinstance(message, dict) for message in messages):
            print("The list of messages is not a list of dictionaries.")
            return False

        # Check if the dictionary has the correct keys# Check if the list of messages is a list of dictionaries with 'role' and 'content' keys
        elif not all("role" in message and "content" in message for message in messages):
            print("The list of messages is not a list of dictionaries with 'role' and 'content' keys.")
            return False

        keys = [key for key in message.keys()]
        if len(keys) > 2:
            raise KeyError(f"The dictionary {message} should only have 2 keys ('role' and 'content').")
        elif len(keys) == 1:
            raise KeyError(f"The dictionary {message} should have 2 keys ('role' and 'content').")
        elif len(keys) == 2:
            if keys == ['role', 'content']:
                continue
            else:
                raise KeyError(f"The dictionary {message} does not have the correct keys. It should have 2 keys ('role' and 'content').")

    else:
        print("The list of messages is correctly formated.")
        return True


messages=[{"role":"user",
           "content":"test", 
           "role":"user2"},
           {"role":"user3",
            "content":"test"}]
pplx_messages_format_validation(messages)