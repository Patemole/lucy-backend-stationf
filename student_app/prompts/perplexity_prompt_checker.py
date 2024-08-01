from typing import List, Dict

def pplx_messages_format_validation(messages: List[Dict[str, str]]) -> bool:

    # Check if the list of messages is a list
    if not isinstance(messages, list):
        raise TypeError("The list of messages is not a list.")
    
    # check message dictionnaries one by one
    for message in messages:

        # Get the keys of the message dictionary
        keys = [key for key in message.keys()]

        # Check if the list of messages is a list of dictionaries
        if not all(isinstance(message, dict) for message in messages):
            raise TypeError("The list of messages is not a list of dictionaries.")

        # Check if the dictionary has the correct keys# Check if the list of messages is a list of dictionaries with 'role' and 'content' keys
        elif not all("role" in message and "content" in message for message in messages):
            raise KeyError("The list of messages is not a list of dictionaries with 'role' and 'content' keys.")

        # check for length of the dictionnary
        elif len(keys) > 2:
            raise KeyError(f"The dictionary {message} should ONLY have 2 keys ('role' and 'content').")
            
        elif len(keys) == 1:
            raise KeyError(f"The dictionary {message} should have 2 keys ('role' and 'content').")
        
        elif len(keys) == 2:
            if keys == ['role', 'content']:
                continue
            else:
                raise KeyError(f"The dictionary {message} does not have the correct keys. It should have 2 keys ('role' and 'content').")
            
    # Check first and last message's roles (system message is optionnal)
    if messages[0]['role'] == "system":

        if messages[1]['role'] != "user":
            raise Exception("After the (optional) system message(s), it should start with a user message. \n e.g. {'role': 'user', 'content': 'Hello!'}")
        elif messages[-1]['role'] != "user":
            raise Exception(f"Last message should be using the exact role key user. \n Check message format of message number {len(messages)}: {messages[-1]}")
        
        i = 1
        expected_role = "user"
        while i < len(messages) - 1:
            if messages[i]['role'] == expected_role:
                expected_role = "assistant" if expected_role == "user" else "user"
            else:
                raise Exception(f"user and assistant roles should be alternating. Check format of message number \n {i}: {messages[i]} \n {i+1}: {messages[i+1]} \n {i+2}: {messages[i+2]}")
            i += 1

    elif messages[0]['role'] == "user":
        if messages[-1]['role'] != "user":
            raise Exception(f"Last message should be using the exact role key user. \n Check message format of message number {len(messages)}: {messages[-1]}")
        
        i = 0
        expected_role = "user"
        while i < len(messages) - 1:
            if messages[i]['role'] == expected_role:
                expected_role = "assistant" if expected_role == "user" else "user"
            else:
                raise Exception(f"user and assistant roles should be alternating. Check format of message number \n {i}: {messages[i]} \n {i+1}: {messages[i+1]} \n {i+2}: {messages[i+2]}")
            i += 1
    
    else:
        raise Exception(f"First message {messages[0]} should be using the role key system or user." + "\n {'role': 'system', 'content': 'Hello!'} \nOR \n {'role': 'user', 'content': 'Hello!'}")
    
    print("Prompt was correctly reformated")


################################## TESTING ###############################################

# messages=[
#     # {"role":"system", "content":"test"},
#     {"role":"user1", "content":"test"},
#     {"role":"assistant", "content":"test"},
#     {"role":"user", "content":"test"},
#     {"role":"user2", "content":"test"},
#     ]

# pplx_messages_format_validation(messages)

################################## TESTING ###############################################