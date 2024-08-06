class ValidationError(Exception):
    pass

class NotAListError(ValidationError):
    pass

class NotListOfDictError(ValidationError):
    pass

class InvalidKeysError(ValidationError):
    pass

class InvalidRoleValueError(ValidationError):
    pass

class InvalidFirstRoleError(ValidationError):
    pass

class InvalidLastRoleError(ValidationError):
    pass

class InvalidRoleSequenceError(ValidationError):
    pass

def pplx_messages_format_validation(messages):
    # Rule 1: Be a list
    if not isinstance(messages, list):
        raise NotAListError("The input is not a list.")
    
    # Rule 2: Be a list of dict
    if not all(isinstance(item, dict) for item in messages):
        raise NotListOfDictError("The list does not contain only dictionaries.")
    
    # Rule 3: Each dict should have exactly 2 keys ("role" and "content") in order
    for item in messages:
        if list(item.keys()) != ["role", "content"]:
            if list(item.keys()) == ["content", "role"]:
                item = {"role": item["role"], "content": item["content"]}
            else:
                raise InvalidKeysError("Each dictionary must have exactly 'role' and 'content' keys in that order.")
    
    # Rule 4: The value of the role key can only be "user", "assistant", or "system"
    valid_roles = {"user", "assistant", "system"}
    if not all(item["role"] in valid_roles for item in messages):
        raise InvalidRoleValueError("The role key can only have values 'user', 'assistant', or 'system'.")
    
    # Rule 5: The first dict role key should be either "user" or "system" but cannot be "assistant"
    if messages[0]["role"] not in {"user", "system"}:
        if messages[0]["role"] == "assistant":
            messages.insert(0, {"role": "user", "content": ""})
        # raise InvalidFirstRoleError("The first role must be 'user' or 'system', but not 'assistant'.")
    
    # Rule 6: The last dict role key should be "user"
    if messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": ""})
        # raise InvalidLastRoleError("The last role must be 'user'.")
    
    # Rule 7: If the role key of the first dict is "system"
    if messages[0]["role"] == "system":
        if len(messages) < 2 or messages[1]["role"] != "user":
            messages.insert(1, {"role": "user", "content": ""})
            print(messages)
            # raise InvalidRoleSequenceError("If the first role is 'system', the second must be 'user'.")
        expected_roles = ["user", "assistant"]
        for i, item in enumerate(messages[1:]):
            if item["role"] != expected_roles[i % 2]:
                messages.insert(i + 1, {"role": expected_roles[i % 2], "content": ""})
                print(messages)
                # raise InvalidRoleSequenceError("Roles must alternate between 'user' and 'assistant' after 'system'.")
      
    # Rule 8: If the role key of the first dict is "user"
    if messages[0]["role"] == "user":
        if len(messages) < 2:
            pass
            # raise InvalidRoleSequenceError("If the first role is 'user', the second must be 'assistant'.")
        expected_roles = ["user", "assistant"]
        for i, item in enumerate(messages[2:]):
            if item["role"] != expected_roles[i % 2]:
                messages.insert(i + 1, {"role": expected_roles[i % 2], "content": ""})
                print(messages)
                # raise InvalidRoleSequenceError("Roles must alternate between 'assistant' and 'user' after 'user'.")
    



# # Example usage
# messages = [
#     {"role": "user", "content": "Hello!"},
#     {"role": "assistant", "content": "Hi there!"},
#     {"role": "user", "content": "How are you?"},
#     {"role": "assistant", "content": "I'm good, thank you! How can I help you today?"},
#     {"role": "user", "content": "I need some assistance with my account."},
#     {"role": "user", "content": "I need some assistance with my account."}
# ]

# try:
#     print(pplx_messages_format_validation(messages))  # Output: True
# except ValidationError as e:
#     print(e)


def run_tests():
    # Test 1: Input is not a list
    try:
        pplx_messages_format_validation("not a list")
    except Exception as e:
        print(e)

    
    # Test 2: Input is not a list of dicts
    try:
        pplx_messages_format_validation(["not a dict"])
    except Exception as e:
        print(e)

    
    # Test 3: Each dict should have exactly 2 keys ("role" and "content")
    try:
        dict = pplx_messages_format_validation([{"content": "Hello", "role": "user"}])
        print(dict)
    except Exception as e:
        print(e)
        
    # Test 4: The value of the role key can only be "user", "assistant", or "system"
    try:
        pplx_messages_format_validation([{"role": "invalid", "content": "Hello"}])
    except Exception as e:
        print(e)
    
    # Test 5: The first dict role key should be either "user" or "system" but cannot be "assistant"
    try:
        pplx_messages_format_validation([{"role": "assistant", "content": "Hello"}])
    except Exception as e:
        print(e)

    
    # Test 6: The last dict role key should be "user"
    try:
        pplx_messages_format_validation([{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}])
    except Exception as e:
        print(e)
    
    # Test 7: If the first role is "system", the second must be "user"
    try:
        pplx_messages_format_validation([{"role": "system", "content": "System message"}, {"role": "assistant", "content": "Hi"}])
    except Exception as e:
        print(e)
    
    # Test 8: If the first role is "system", roles must alternate starting with "user" after the second message
    try:
        pplx_messages_format_validation([
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "user", "content": "Another user message"}
        ])
    except Exception as e:
        print(e)

    
    # Test 9: If the first role is "user", the second must be "assistant"
    try:
        pplx_messages_format_validation([{"role": "user", "content": "Hello"}, {"role": "user", "content": "Hi"}])
    except Exception as e:
        print(e)
    
    # Test 10: If the first role is "user", roles must alternate starting with "assistant" after the first message
    try:
        pplx_messages_format_validation([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "assistant", "content": "Another assistant message"}
        ])
    except Exception as e:
        print(e)

    
    # Test 11: Valid sequence starting with "user"
    try:
        pplx_messages_format_validation([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good, thank you!"},
            {"role": "user", "content": "Great!"}
        ])
    except Exception as e:
        print(e)

    
    # Test 12: Valid sequence starting with "system"
    try:
        pplx_messages_format_validation([
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good, thank you!"},
            {"role": "user", "content": "Great!"}
        ])
    except Exception as e:
        print(e)


# Run tests
# run_tests()
