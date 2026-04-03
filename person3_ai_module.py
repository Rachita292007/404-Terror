"""
PERSON 3: AI Module - Simpler version without ChromaDB
Use this if you want a lightweight version
"""

import re
from datetime import datetime
from typing import List, Dict

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract prices, dates, quantities from text"""
    entities = {"prices": [], "dates": [], "quantities": []}
    
    # Extract prices
    price_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
    entities["prices"] = re.findall(price_pattern, text)
    
    # Extract dates
    date_pattern = r'\d{4}-\d{1,2}-\d{1,2}'
    entities["dates"] = re.findall(date_pattern, text)
    
    # Extract quantities
    qty_pattern = r'\d+\s*(?:units|pieces|items)'
    entities["quantities"] = re.findall(qty_pattern, text, re.I)
    
    return entities

def detect_conflicts_simple(documents: List[Dict]) -> List[Dict]:
    """Simple conflict detection"""
    all_prices = []
    for doc in documents:
        entities = extract_entities(doc["text"])
        for price in entities["prices"]:
            all_prices.append({
                "value": price,
                "source": doc["source"],
                "date": doc["date"]
            })
    
    unique_prices = list(set([p["value"] for p in all_prices]))
    if len(unique_prices) > 1:
        all_prices.sort(key=lambda x: x["date"], reverse=True)
        return [{
            "type": "prices",
            "values": unique_prices,
            "recommended": all_prices[0]["value"],
            "source": all_prices[0]["source"]
        }]
    
    return []

print("✅ AI Module loaded successfully!")
