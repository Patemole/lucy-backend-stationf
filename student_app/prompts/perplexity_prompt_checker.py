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
    
    # Rule 3: Each dict should have exactly 2 keys ("role" and "content")
    for item in messages:
        if set(item.keys()) != {"role", "content"}:
            raise InvalidKeysError("Each dictionary must have exactly 'role' and 'content' keys.")
    
    # Rule 4: The value of the role key can only be "user", "assistant", or "system"
    valid_roles = {"user", "assistant", "system"}
    if not all(item["role"] in valid_roles for item in messages):
        raise InvalidRoleValueError("The role key can only have values 'user', 'assistant', or 'system'.")
    
    # Rule 5: The first dict role key should be either "user" or "system" but cannot be "assistant"
    if messages[0]["role"] not in {"user", "system"}:
        raise InvalidFirstRoleError("The first role must be 'user' or 'system', but not 'assistant'.")
    
    # Rule 6: The last dict role key should be "user"
    if messages[-1]["role"] != "user":
        raise InvalidLastRoleError("The last role must be 'user'.")
    
    # Rule 7: If the role key of the first dict is "system"
    if messages[0]["role"] == "system":
        if len(messages) < 2 or messages[1]["role"] != "user":
            raise InvalidRoleSequenceError("If the first role is 'system', the second must be 'user'.")
        expected_roles = ["user", "assistant"]
        for i, item in enumerate(messages[1:], start=2):
            if item["role"] != expected_roles[i % 2]:
                raise InvalidRoleSequenceError("Roles must alternate between 'user' and 'assistant' after 'system'.")
    
    # Rule 8: If the role key of the first dict is "user"
    if messages[0]["role"] == "user":
        if len(messages) < 2 or messages[1]["role"] != "assistant":
            raise InvalidRoleSequenceError("If the first role is 'user', the second must be 'assistant'.")
        expected_roles = ["user", "assistant"]
        for i, item in enumerate(messages[2:], start=2):
            if item["role"] != expected_roles[i % 2]:
                raise InvalidRoleSequenceError("Roles must alternate between 'assistant' and 'user' after 'user'.")
    
    return True

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
    except NotAListError:
        print("Test 1 passed.")
    except ValidationError:
        print("Test 1 failed: wrong exception type.")
    
    # Test 2: Input is not a list of dicts
    try:
        pplx_messages_format_validation(["not a dict"])
    except NotListOfDictError:
        print("Test 2 passed.")
    except ValidationError:
        print("Test 2 failed: wrong exception type.")
    
    # Test 3: Each dict should have exactly 2 keys ("role" and "content")
    try:
        pplx_messages_format_validation([{"role": "user"}])
    except InvalidKeysError:
        print("Test 3 passed.")
    except ValidationError:
        print("Test 3 failed: wrong exception type.")
    
    # Test 4: The value of the role key can only be "user", "assistant", or "system"
    try:
        pplx_messages_format_validation([{"role": "invalid", "content": "Hello"}])
    except InvalidRoleValueError:
        print("Test 4 passed.")
    except ValidationError:
        print("Test 4 failed: wrong exception type.")
    
    # Test 5: The first dict role key should be either "user" or "system" but cannot be "assistant"
    try:
        pplx_messages_format_validation([{"role": "assistant", "content": "Hello"}])
    except InvalidFirstRoleError:
        print("Test 5 passed.")
    except ValidationError:
        print("Test 5 failed: wrong exception type.")
    
    # Test 6: The last dict role key should be "user"
    try:
        pplx_messages_format_validation([{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}])
    except InvalidLastRoleError:
        print("Test 6 passed.")
    except ValidationError:
        print("Test 6 failed: wrong exception type.")
    
    # Test 7: If the first role is "system", the second must be "user"
    try:
        pplx_messages_format_validation([{"role": "system", "content": "System message"}, {"role": "assistant", "content": "Hi"}])
    except InvalidRoleSequenceError:
        print("Test 7 passed.")
    except ValidationError:
        print("Test 7 failed: wrong exception type.")
    
    # Test 8: If the first role is "system", roles must alternate starting with "user" after the second message
    try:
        pplx_messages_format_validation([
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "user", "content": "Another user message"}
        ])
    except InvalidRoleSequenceError:
        print("Test 8 passed.")
    except ValidationError:
        print("Test 8 failed: wrong exception type.")
    
    # Test 9: If the first role is "user", the second must be "assistant"
    try:
        pplx_messages_format_validation([{"role": "user", "content": "Hello"}, {"role": "user", "content": "Hi"}])
    except InvalidRoleSequenceError:
        print("Test 9 passed.")
    except ValidationError:
        print("Test 9 failed: wrong exception type.")
    
    # Test 10: If the first role is "user", roles must alternate starting with "assistant" after the first message
    try:
        pplx_messages_format_validation([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "assistant", "content": "Another assistant message"}
        ])
    except InvalidRoleSequenceError:
        print("Test 10 passed.")
    except ValidationError:
        print("Test 10 failed: wrong exception type.")
    
    # Test 11: Valid sequence starting with "user"
    try:
        assert pplx_messages_format_validation([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good, thank you!"},
            {"role": "user", "content": "Great!"}
        ])
        print("Test 11 passed.")
    except ValidationError:
        print("Test 11 failed.")
    
    # Test 12: Valid sequence starting with "system"
    try:
        assert pplx_messages_format_validation([
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm good, thank you!"},
            {"role": "user", "content": "Great!"}
        ])
        print("Test 12 passed.")
    except ValidationError:
        print("Test 12 failed.")

# Run tests
# run_tests()
