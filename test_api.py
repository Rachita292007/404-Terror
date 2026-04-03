import requests
import json

print("="*60)
print("🧠 Testing LLM Server")
print("="*60)

# Test data with CONFLICT (3 different prices)
test_data = {
    "query": "What is the price?",
    "documents": [
        {
            "text": "Product SKU-100 price is $100",
            "source": "old_catalog.pdf",
            "date": "2024-01-15"
        },
        {
            "text": "Updated pricing: Now $120 per unit",
            "source": "price_update.xlsx",
            "date": "2024-02-20"
        },
        {
            "text": "Special offer: $110 for bulk orders",
            "source": "sales_email.json",
            "date": "2024-03-01"
        }
    ]
}

print(f"📡 Sending request to: http://10.23.47.61:5002/ask")
print(f"📝 Question: {test_data['query']}")
print(f"📄 Documents: {len(test_data['documents'])} files")
print("="*60)

try:
    response = requests.post(
        "http://10.23.47.61:5002/ask",
        json=test_data,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ LLM RESPONSE:")
        print("="*60)
        print(result["answer"])
        print("="*60)
        print(f"\n📚 Sources: {', '.join(result['sources'])}")
        print(f"⚠️  Conflicts found: {result['conflicts_found']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n💡 Make sure llm_server.py is running in another terminal!")
    