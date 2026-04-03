import requests

# This is correct - POST request
response = requests.post(
    "http://10.23.47.61:5002/ask",
    json={"query": "test", "documents": [{"text": "test", "source": "test.pdf"}]}
)

print(response.status_code)  # Should be 200
print(response.json())