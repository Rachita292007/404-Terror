import requests

url = "http://10.23.47.61:5002/ask"

# Test PDF content
test_docs = [
    {
        "text": "Product SKU-100 price is $100. Valid until March 15, 2024. 50 units in stock.",
        "source": "contract_q1.pdf",
        "type": "PDF",
        "date": "2024-01-15"
    },
    {
        "text": "Updated pricing: SKU-100 now $120 per unit. Effective February 20, 2024. Stock: 75 units.",
        "source": "price_update.pdf",
        "type": "PDF",
        "date": "2024-02-20"
    },
    {
        "text": "Special offer: SKU-100 at $110 for bulk orders. Valid until March 31, 2024.",
        "source": "special_offer.pdf",
        "type": "PDF",
        "date": "2024-03-01"
    }
]

response = requests.post(url, json={
    "query": "What is the current price of SKU-100?",
    "documents": test_docs
})

print(response.json()["answer"])