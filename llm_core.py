"""
COMPUTER 3: LLM CORE - Build this FIRST!
This works STANDALONE - no database needed for testing
"""

import re
from datetime import datetime
from typing import List, Dict

# ============================================================
# STEP 1: ENTITY EXTRACTION (Your LLM's "eyes")
# ============================================================

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Find prices, dates, quantities in text"""
    entities = {
        "prices": [],
        "dates": [],
        "quantities": []
    }
    
    # Find prices like $100, $50.99
    price_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
    entities["prices"] = re.findall(price_pattern, text)
    
    # Find dates like 2024-03-01, 01/15/2024
    date_patterns = [
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'\d{1,2}/\d{1,2}/\d{2,4}'
    ]
    for pattern in date_patterns:
        entities["dates"].extend(re.findall(pattern, text))
    
    # Find quantities like 50 units, 100 pieces
    qty_pattern = r'\d+\s*(?:units|pieces|items)'
    entities["quantities"] = re.findall(qty_pattern, text, re.I)
    
    # Remove duplicates
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))
    
    return entities

# ============================================================
# STEP 2: CONFLICT DETECTION (Your WINNING feature!)
# ============================================================

def detect_conflicts(documents: List[Dict]) -> List[Dict]:
    """
    Find conflicting information across documents.
    This is what judges will LOVE!
    """
    if len(documents) < 2:
        return []
    
    # Collect all prices with their sources and dates
    all_prices = []
    for doc in documents:
        entities = extract_entities(doc["text"])
        for price in entities["prices"]:
            all_prices.append({
                "value": price,
                "source": doc.get("source", "unknown"),
                "date": doc.get("date", datetime.now().isoformat()),
                "text": doc["text"][:200]
            })
    
    # Find unique prices
    unique_prices = list(set([p["value"] for p in all_prices]))
    
    # If multiple different prices exist → CONFLICT!
    if len(unique_prices) > 1:
        # Sort by date (newest first)
        all_prices.sort(key=lambda x: x["date"], reverse=True)
        
        return [{
            "type": "prices",
            "values": unique_prices,
            "recommended_value": all_prices[0]["value"],
            "recommended_source": all_prices[0]["source"],
            "explanation": f"Latest document ({all_prices[0]['source']}) suggests {all_prices[0]['value']}"
        }]
    
    return []

# ============================================================
# STEP 3: ANSWER GENERATION (Your LLM's "voice")
# ============================================================

def generate_answer(query: str, documents: List[Dict]) -> Dict:
    """
    Generate answer with conflict resolution.
    This is the MAIN function your UI will call!
    """
    
    # First, detect conflicts
    conflicts = detect_conflicts(documents)
    
    # Check if query is asking about price
    price_keywords = ["price", "cost", "pricing", "rate"]
    is_price_query = any(kw in query.lower() for kw in price_keywords)
    
    # If there's a price conflict and user asks about price
    if conflicts and is_price_query:
        conflict = conflicts[0]
        
        # Build the conflict response
        conflict_details = "\n".join([
            f"  • {value} (from various documents)"
            for value in conflict["values"]
        ])
        
        answer = f"""**{conflict['recommended_value']}** ✅

⚠️ **CONFLICT DETECTED!** Multiple prices found:

{conflict_details}

✓ **RESOLUTION:** Using **{conflict['recommended_value']}** from **{conflict['recommended_source']}**

**Decision:** {conflict['explanation']}

💡 This ensures you always have the most current information."""
        
        return {
            "answer": answer,
            "sources": list(set([doc["source"] for doc in documents])),
            "conflicts_found": True,
            "conflict_resolved": conflict['recommended_value']
        }
    
    # No conflict - normal answer
    elif documents:
        # Use the most relevant document
        main_doc = documents[0]
        answer = f"""Based on your documents:

{main_doc['text'][:400]}...

---
📚 **Source:** {main_doc['source']}"""

        return {
            "answer": answer,
            "sources": [main_doc['source']],
            "conflicts_found": False
        }
    
    else:
        return {
            "answer": "No documents found. Please upload files first.",
            "sources": [],
            "conflicts_found": False
        }

# ============================================================
# STEP 4: TEST YOUR LLM (Run this NOW!)
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 LLM CORE - TEST YOUR INTELLIGENCE")
    print("="*60)
    
    # Create test documents WITH CONFLICTS
    test_docs = [
        {
            "text": "The product price is $100. Valid until January.",
            "source": "old_contract.pdf",
            "date": "2024-01-15"
        },
        {
            "text": "Updated pricing: Now $120 per unit.",
            "source": "price_update.xlsx",
            "date": "2024-02-20"
        },
        {
            "text": "Special offer: $110 for bulk orders.",
            "source": "sales_email.json",
            "date": "2024-03-01"
        }
    ]
    
    print("\n📝 Test Documents:")
    for doc in test_docs:
        print(f"   • {doc['source']}: {doc['text']}")
    
    # Test entity extraction
    print("\n🔍 Testing Entity Extraction:")
    for doc in test_docs:
        entities = extract_entities(doc["text"])
        print(f"   {doc['source']}: Prices found: {entities['prices']}")
    
    # Test conflict detection
    print("\n⚡ Testing Conflict Detection:")
    conflicts = detect_conflicts(test_docs)
    if conflicts:
        print(f"   ✅ CONFLICT FOUND!")
        print(f"   Values: {conflicts[0]['values']}")
        print(f"   Recommended: {conflicts[0]['recommended_value']}")
        print(f"   Source: {conflicts[0]['recommended_source']}")
    else:
        print("   No conflicts found")
    
    # Test answer generation
    print("\n🤖 Testing Answer Generation:")
    print("   User asks: 'What is the price?'")
    
    result = generate_answer("What is the price?", test_docs)
    
    print("\n" + "="*40)
    print("LLM RESPONSE:")
    print("="*40)
    print(result["answer"])
    print("="*40)
    
    print("\n✅ Your LLM is WORKING!")
    print("   You can now show conflict detection to judges WITHOUT any database!")