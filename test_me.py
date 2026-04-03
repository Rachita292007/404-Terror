import requests

url = "http://10.23.47.61:5002/ask"

data = {
    "query": "What is the price?",
    "documents": [
        {"text": "Price $100", "source": "old.pdf", "date": "2024-01-01"},
        {"text": "Price $120", "source": "new.xlsx", "date": "2024-02-01"},
        {"text": "Price $110", "source": "email.json", "date": "2024-03-01"}
    ]
}

print("Sending request...")
response = requests.post(url, json=data)
print("Status:", response.status_code)
print("Response:")
print(response.json()["answer"])