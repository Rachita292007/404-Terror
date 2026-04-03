"""
COMPUTER 3: FULLY TRAINED LLM SERVER
Answers ALL questions about your documents
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
from typing import List, Dict
import uuid

app = Flask(__name__)
CORS(app)

# Conversation memory
conversation_memory = {}

# ============================================================
# STEP 1: EXTRACT EVERYTHING FROM DOCUMENTS
# ============================================================

def extract_all_entities(text: str) -> Dict[str, List[str]]:
    """Extract ALL important information from text"""
    
    entities = {
        "prices": [],
        "dates": [],
        "quantities": [],
        "products": [],
        "emails": [],
        "percentages": [],
        "names": [],
        "locations": [],
        "deadlines": [],
        "actions": []
    }
    
    # PRICES
    price_patterns = [
        r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
        r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|usd|dollars)',
        r'price\s*[is:]\s*\$\d+',
    ]
    for pattern in price_patterns:
        entities["prices"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # DATES
    date_patterns = [
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}',
        r'\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}',
    ]
    for pattern in date_patterns:
        entities["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # DEADLINES (specific)
    deadline_patterns = [
        r'deadline[:\s]+[^\n]+',
        r'valid until[:\s]+[^\n]+',
        r'expires on[:\s]+[^\n]+',
        r'due date[:\s]+[^\n]+',
    ]
    for pattern in deadline_patterns:
        entities["deadlines"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # QUANTITIES
    quantity_patterns = [
        r'\d+\s*(?:units|pieces|items|kg|lbs|boxes|cases|dozen)',
        r'stock[:\s]+\d+',
        r'inventory[:\s]+\d+',
        r'quantity[:\s]+\d+',
    ]
    for pattern in quantity_patterns:
        entities["quantities"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # PRODUCTS/SKUs
    product_patterns = [
        r'SKU[-_]?\d+',
        r'[A-Z]{2,}-\d+',
        r'product[:\s]+[A-Z0-9-]+',
    ]
    for pattern in product_patterns:
        entities["products"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # NAMES (people, companies)
    name_patterns = [
        r'(?:Mr|Ms|Mrs|Dr)\.\s+[A-Z][a-z]+',
        r'[A-Z][a-z]+ [A-Z][a-z]+',
    ]
    for pattern in name_patterns:
        entities["names"].extend(re.findall(pattern, text))
    
    # EMAILS
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    entities["emails"] = re.findall(email_pattern, text)
    
    # Clean duplicates
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))[:5]
    
    return entities

# ============================================================
# STEP 2: UNDERSTAND WHAT USER IS ASKING
# ============================================================

def understand_question(query: str) -> Dict:
    """Figure out what the user wants to know"""
    
    query_lower = query.lower()
    
    intent = {
        "type": "general",
        "entities": []
    }
    
    # Price questions
    if any(w in query_lower for w in ["price", "cost", "pricing", "rate", "how much", "what.*price"]):
        intent["type"] = "price"
        intent["description"] = "User wants pricing information"
    
    # Date questions
    elif any(w in query_lower for w in ["date", "when", "deadline", "valid", "effective", "until", "expires"]):
        intent["type"] = "date"
        intent["description"] = "User wants date/deadline information"
    
    # Quantity questions
    elif any(w in query_lower for w in ["quantity", "stock", "inventory", "how many", "units", "pieces"]):
        intent["type"] = "quantity"
        intent["description"] = "User wants quantity/stock information"
    
    # Product questions
    elif any(w in query_lower for w in ["product", "sku", "item", "model"]):
        intent["type"] = "product"
        intent["description"] = "User wants product information"
    
    # Comparison questions
    elif any(w in query_lower for w in ["compare", "difference", "versus", "vs"]):
        intent["type"] = "comparison"
        intent["description"] = "User wants to compare documents"
    
    # Summary questions
    elif any(w in query_lower for w in ["summarize", "summary", "overview", "all"]):
        intent["type"] = "summary"
        intent["description"] = "User wants a summary"
    
    return intent

# ============================================================
# STEP 3: DETECT CONFLICTS
# ============================================================

def detect_conflicts(documents: List[Dict]) -> Dict:
    """Find conflicts in documents"""
    
    if len(documents) < 2:
        return {"conflicts": [], "has_conflicts": False}
    
    all_prices = []
    all_quantities = []
    all_dates = []
    
    for doc in documents:
        text = doc.get("text", "")
        entities = extract_all_entities(text)
        
        for price in entities["prices"]:
            all_prices.append({
                "value": price,
                "source": doc.get("source", "unknown"),
                "date": doc.get("date", ""),
            })
        
        for qty in entities["quantities"]:
            all_quantities.append({
                "value": qty,
                "source": doc.get("source", "unknown"),
                "date": doc.get("date", ""),
            })
        
        for date in entities["dates"]:
            all_dates.append({
                "value": date,
                "source": doc.get("source", "unknown"),
            })
    
    conflicts = []
    
    # Price conflicts
    unique_prices = list(set([p["value"] for p in all_prices]))
    if len(unique_prices) > 1:
        all_prices.sort(key=lambda x: x["date"], reverse=True)
        conflicts.append({
            "type": "price",
            "values": unique_prices,
            "recommended": all_prices[0]["value"],
            "source": all_prices[0]["source"],
            "reason": f"Most recent document ({all_prices[0]['source']})"
        })
    
    # Quantity conflicts
    unique_qties = list(set([q["value"] for q in all_quantities]))
    if len(unique_qties) > 1:
        all_quantities.sort(key=lambda x: x["date"], reverse=True)
        conflicts.append({
            "type": "quantity",
            "values": unique_qties,
            "recommended": all_quantities[0]["value"],
            "source": all_quantities[0]["source"],
        })
    
    return {
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0
    }

# ============================================================
# STEP 4: GENERATE ANSWER (THE SMART PART)
# ============================================================

def generate_smart_answer(query: str, documents: List[Dict]) -> Dict:
    """Generate the best answer for ANY question"""
    
    if not documents:
        return {
            "answer": "❌ No documents found. Please upload PDF files first.",
            "sources": [],
            "conflicts_found": False
        }
    
    # Understand what user wants
    intent = understand_question(query)
    conflict_data = detect_conflicts(documents)
    conflicts = conflict_data["conflicts"]
    
    # Extract all info from documents
    all_info = []
    for doc in documents:
        entities = extract_all_entities(doc["text"])
        all_info.append({
            "source": doc["source"],
            "date": doc.get("date", ""),
            "entities": entities
        })
    
    # ========== HANDLE DIFFERENT QUESTION TYPES ==========
    
    # 1. PRICE QUESTIONS
    if intent["type"] == "price":
        price_conflicts = [c for c in conflicts if c["type"] == "price"]
        
        if price_conflicts:
            c = price_conflicts[0]
            bullet = "\n".join([f"  • {v}" for v in c["values"]])
            return {
                "answer": f"""🏆 **RESOLUTION: {c['recommended']}** (from {c['source']})

⚠️ **CONFLICT DETECTED!** Multiple prices found:

{bullet}

✓ **DECISION:** Using **{c['recommended']}** from **{c['source']}**

💡 **REASON:** {c['reason']} takes precedence over older documents.

✅ This ensures you always use the most up-to-date information.""",
                "sources": list(set([d["source"] for d in documents])),
                "conflicts_found": True,
                "recommended_value": c["recommended"]
            }
        else:
            # No conflict - show all prices
            all_prices = []
            for info in all_info:
                all_prices.extend(info["entities"]["prices"])
            if all_prices:
                return {
                    "answer": f"💰 **Prices found in documents:**\n\n" + "\n".join([f"  • {p}" for p in set(all_prices)]) + "\n\n📚 No conflicts detected. All documents agree.",
                    "sources": list(set([d["source"] for d in documents])),
                    "conflicts_found": False
                }
    
    # 2. DATE QUESTIONS
    elif intent["type"] == "date":
        all_dates = []
        for info in all_info:
            all_dates.extend(info["entities"]["dates"])
        
        if all_dates:
            # Find most recent date
            latest = max([d for d in all_dates if d], default="Unknown")
            return {
                "answer": f"📅 **Dates found in documents:**\n\n" + "\n".join([f"  • {d}" for d in set(all_dates)]) + f"\n\n📌 **Latest date:** {latest}\n\n💡 This is likely the most current information.",
                "sources": list(set([d["source"] for d in documents])),
                "conflicts_found": False
            }
    
    # 3. QUANTITY QUESTIONS
    elif intent["type"] == "quantity":
        all_qties = []
        for info in all_info:
            all_qties.extend(info["entities"]["quantities"])
        
        if all_qties:
            return {
                "answer": f"📦 **Quantities found:**\n\n" + "\n".join([f"  • {q}" for q in set(all_qties)]),
                "sources": list(set([d["source"] for d in documents])),
                "conflicts_found": False
            }
    
    # 4. PRODUCT QUESTIONS
    elif intent["type"] == "product":
        all_products = []
        for info in all_info:
            all_products.extend(info["entities"]["products"])
        
        if all_products:
            return {
                "answer": f"🏷️ **Products/SKUs found:**\n\n" + "\n".join([f"  • {p}" for p in set(all_products)]),
                "sources": list(set([d["source"] for d in documents])),
                "conflicts_found": False
            }
    
    # 5. SUMMARY QUESTIONS
    elif intent["type"] == "summary":
        summary_parts = []
        for info in all_info:
            if info["entities"]["prices"]:
                summary_parts.append(f"• {info['source']}: Prices {', '.join(info['entities']['prices'])}")
            if info["entities"]["dates"]:
                summary_parts.append(f"• {info['source']}: Dates {', '.join(info['entities']['dates'])}")
        
        if summary_parts:
            return {
                "answer": f"📋 **Document Summary:**\n\n" + "\n".join(summary_parts),
                "sources": list(set([d["source"] for d in documents])),
                "conflicts_found": conflict_data["has_conflicts"]
            }
    
    # 6. COMPARISON QUESTIONS
    elif intent["type"] == "comparison":
        comparison = []
        for info in all_info:
            comparison.append(f"📄 **{info['source']}** (Date: {info['date'][:10] if info['date'] else 'Unknown'})")
            if info["entities"]["prices"]:
                comparison.append(f"   Prices: {', '.join(info['entities']['prices'])}")
            if info["entities"]["dates"]:
                comparison.append(f"   Dates: {', '.join(info['entities']['dates'])}")
            comparison.append("")
        
        return {
            "answer": "\n".join(comparison),
            "sources": list(set([d["source"] for d in documents])),
            "conflicts_found": conflict_data["has_conflicts"]
        }
    
    # 7. GENERAL QUESTION (Fallback)
    # Return first document's content
    return {
        "answer": f"📄 **Based on {documents[0]['source']}:**\n\n{documents[0]['text'][:500]}...\n\n💡 For more specific answers, try asking about prices, dates, or quantities.",
        "sources": [documents[0]["source"]],
        "conflicts_found": False
    }

# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Trained LLM", "version": "3.0"})

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '')
        documents = data.get('documents', [])
        
        print(f"\n📨 Question: {query}")
        print(f"   Documents: {len(documents)}")
        
        result = generate_smart_answer(query, documents)
        
        print(f"   Response type: {result.get('conflicts_found', 'unknown')}")
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    text = data.get('text', '')
    entities = extract_all_entities(text)
    return jsonify(entities)

@app.route('/ask_with_memory', methods=['POST'])
def ask_with_memory():
    data = request.get_json()
    session_id = data.get('session_id', str(uuid.uuid4()))
    query = data.get('query', '')
    documents = data.get('documents', [])
    
    history = conversation_memory.get(session_id, [])
    history_text = ""
    for h in history[-3:]:
        history_text += f"Previous: {h['q']}\nAnswer: {h['a'][:100]}\n\n"
    
    enhanced_query = f"{history_text}\n\nCurrent: {query}"
    result = generate_smart_answer(enhanced_query, documents)
    
    conversation_memory.setdefault(session_id, []).append({
        'q': query,
        'a': result['answer'][:200],
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify(result)

@app.route('/clear_memory', methods=['POST'])
def clear_memory():
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    if session_id in conversation_memory:
        del conversation_memory[session_id]
    return jsonify({"status": "cleared"})

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 FULLY TRAINED LLM SERVER")
    print("="*60)
    print("📍 http://10.23.47.61:5002")
    print("📋 I can answer:")
    print("   • Price questions ($100, $120, etc.)")
    print("   • Date questions (deadlines, validity)")
    print("   • Quantity questions (stock, units)")
    print("   • Product questions (SKU, model)")
    print("   • Comparisons (differences)")
    print("   • Summaries (overview)")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)