"""
Arth-Sathi - OMNICHANNEL TELEGRAM AGENT
Runs alongside server.py and sme01_ui.py
"""

import telebot
import requests
import fitz  # PyMuPDF
import json
import openpyxl
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================
# 🚨 PASTE YOUR BOTFATHER TOKEN HERE 🚨
BOT_TOKEN = "8640026170:AAFAF4inCan0USYr9CqvGJ5xNRei513Tk94"  

# Local LLM Server Endpoint
LLM_URL = "http://localhost:5002/ask"

# Initialize the Bot
bot = telebot.TeleBot(BOT_TOKEN)
print("🤖 Arth-Sathi Bot is waking up...")

# ==========================================
# 2. THE MEMORY BANK (Knowledge Base Loader)
# ==========================================
def load_local_files():
    docs = []
    
    # Define the path to the dedicated knowledge base folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_folder = os.path.join(base_dir, "knowledge_base")
    
    # Create the folder if it doesn't exist yet
    if not os.path.exists(kb_folder):
        os.makedirs(kb_folder)
        print(f"📁 Created new folder at: {kb_folder}")
        print("⚠️ WARNING: Your knowledge_base folder is empty. Please add PDFs or Excel files to it.")
        return docs
    
    # Scan the folder and extract text
    for filename in os.listdir(kb_folder):
        filepath = os.path.join(kb_folder, filename)
        
        try:
            # Parse PDFs
            if filename.endswith('.pdf'):
                doc = fitz.open(filepath)
                for page_num, page in enumerate(doc, 1):
                    text = page.get_text().strip()
                    if text:
                        docs.append({"text": text, "source": filename, "type": "PDF"})
            
            # Parse Excel (ignoring temporary lock files that start with ~)
            elif filename.endswith('.xlsx') and not filename.startswith('~'):
                wb = openpyxl.load_workbook(filepath, data_only=True)
                ws = wb.active
                for row in ws.iter_rows(values_only=True):
                    row_vals = [str(c) if c is not None else "" for c in row]
                    row_text = " | ".join(row_vals)
                    if row_text.strip():
                        docs.append({"text": row_text, "source": filename, "type": "Excel"})
            
            # Parse JSON Emails
            elif filename.endswith('.json'):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    email_text = f"FROM: {data.get('from', 'N/A')}\nSUBJECT: {data.get('subject', 'N/A')}\nBODY: {data.get('body', '')}"
                    docs.append({"text": email_text.strip(), "source": filename, "type": "Email"})
                    
        except Exception as e:
            print(f"⚠️ Could not read {filename}: {e}")
            
    return docs

# Load the memory when the script starts
print("📂 Scanning Knowledge Base folder...")
bot_memory = load_local_files()
print(f"✅ Loaded {len(bot_memory)} document chunks into bot memory.")

# ==========================================
# 3. TELEGRAM MESSAGE HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to Arth-Sathi AI!**\n\n"
        "I am your mobile procurement assistant. You can ask me about prices, "
        "contracts, or inventory levels for our registered vendors.\n\n"
        "Try asking: *What is the price of Premium Mawa?*"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def answer_question(message):
    # Safety check: Prevent crashing if memory is empty
    if len(bot_memory) == 0:
        bot.reply_to(message, "❌ **Error:** No documents loaded. Please add files to the `knowledge_base` folder and restart the bot.", parse_mode="Markdown")
        return

    # Send a "Thinking..." status message
    status_msg = bot.reply_to(message, "🧠 _Scanning knowledge base..._", parse_mode="Markdown")
    
    try:
        # Call your local LLM Server
        response = requests.post(
            LLM_URL,
            json={"query": message.text, "documents": bot_memory, "mode": "private"},
            timeout=40
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "I couldn't find an answer.")
            
            # Format the output for Telegram
            final_reply = f"**Answer:**\n{answer}\n\n"
            
            if data.get("conflicts_found"):
                final_reply = "⚠️ **DISCREPANCY DETECTED** ⚠️\n\n" + final_reply
                
            if data.get("sources"):
                final_reply += f"📄 *Sources:* {', '.join(data['sources'])}"
                
            # Edit the "Thinking..." message with the final answer
            bot.edit_message_text(final_reply, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ Backend server error (Status: {response.status_code}). Is `server.py` running?", chat_id=message.chat.id, message_id=status_msg.message_id)
            
    except requests.exceptions.ConnectionError:
        bot.edit_message_text("❌ Cannot connect to backend. Please make sure `server.py` is running on port 5002.", chat_id=message.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ An unexpected error occurred: {e}", chat_id=message.chat.id, message_id=status_msg.message_id)

# ==========================================
# 4. START THE BOT ENGINE
# ==========================================
if __name__ == "__main__":
    print("🚀 Arth-Sathi Telegram Bot is LIVE! Waiting for messages...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped manually.")