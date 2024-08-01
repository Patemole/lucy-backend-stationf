from typing import List, Dict

def pplx_messages_format_validation(messages: List[Dict[str, str]]) -> bool:

    valid_format = False

    # Check if the list of messages is a list
    if not isinstance(messages, list):
        print("The list of messages is not a list.")
        return valid_format
    
    # check message dictionnaries one by one
    for message in messages:

        # Get the keys of the message dictionary
        keys = [key for key in message.keys()]

        # Check if the list of messages is a list of dictionaries
        if not all(isinstance(message, dict) for message in messages):
            print("The list of messages is not a list of dictionaries.")
            return valid_format

        # Check if the dictionary has the correct keys# Check if the list of messages is a list of dictionaries with 'role' and 'content' keys
        elif not all("role" in message and "content" in message for message in messages):
            print("The list of messages is not a list of dictionaries with 'role' and 'content' keys.")
            return valid_format

        elif len(keys) > 2:
            raise KeyError(f"The dictionary {message} should ONLY have 2 keys ('role' and 'content').")
            
        
        elif len(keys) == 1:
            raise KeyError(f"The dictionary {message} should have 2 keys ('role' and 'content').")
        
        elif len(keys) == 2:
            if keys == ['role', 'content']:
                continue
            else:
                raise KeyError(f"The dictionary {message} does not have the correct keys. It should have 2 keys ('role' and 'content').")


################################## TESTING ###############################################

messages=[{"role":"user",
           "content":"test", 
           "role":"user2"},
           {"role":"user3",
            "content":"test"}]
if pplx_messages_format_validation(messages) == True:
    print("The list of messages was correctly formated.")
else:
    print("WARNING: The list of messages was not correctly formated.")

################################## TESTING ###############################################