
def call_deepsearch_api(query):
    """
    Calls jina's deepsearch api to handle complex queries requiring advanced reasoning.
    """
    url = "https://deepsearch.jina.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    # build your data payload
    data = {
        "model": "jina-deepsearch-v1",
        "messages": [
            {"role": "user", "content": "Hi!"},
            {"role": "assistant", "content": "Hi, how can I help you?"},
            {"role": "user", "content": query}
        ],
        "stream": True,
        "reasoning_effort": "medium"
    }

    # post the request
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    return response.text