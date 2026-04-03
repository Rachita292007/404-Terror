import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openpyxl import Workbook

# 1. Setup Local Project Path
# This gets the directory where THIS script is saved
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"📁 Target Project Folder: {current_dir}")

# ============================================================
# 1. CREATE PDF (Supplier Agreement)
# ============================================================
pdf_file = os.path.join(current_dir, "contract.pdf")
c = canvas.Canvas(pdf_file, pagesize=letter)
c.setFont("Helvetica-Bold", 16)
c.drawString(100, 750, "SUPPLIER AGREEMENT - Soham Sweets & Dairy")
c.setFont("Helvetica", 12)
c.drawString(100, 730, "Date: January 15, 2026")
c.drawString(100, 715, "Vendor: PureMilk Logistics | Client: Soham Sweets")

lines = [
    "Terms and Conditions:",
    "1. Product Pricing: Standard 'Premium Mawa' is set at $45.00 per kg.",
    "2. Bulk Discount: Orders exceeding 500 kg receive a 10% discount.",
    "3. Delivery: Guaranteed within 14 business days.",
    "4. Warranty: All dairy products come with a standard 12-month quality guarantee."
]

y = 680
for line in lines:
    c.drawString(100, y, line)
    y -= 20
c.save()
print(f"✅ Created: {pdf_file}")

# ============================================================
# 2. CREATE EXCEL (Inventory Report)
# ============================================================
xlsx_file = os.path.join(current_dir, "product_inventory.xlsx")
wb = Workbook()
ws = wb.active
ws.title = "Inventory_Report"

data = [
    ["Product Name", "SKU", "Unit Price", "Stock (kg)", "Last Restock"],
    ["Premium Mawa", "SKU-MAWA-01", 45.00, 1200, "2026-01-10"],
    ["Desi Ghee", "SKU-GHEE-05", 20.00, 3500, "2026-02-15"],
    ["Kesar Box", "SKU-KESAR-09", 150.00, 450, "2026-03-01"]
]

for row in data:
    ws.append(row)
wb.save(xlsx_file)
print(f"✅ Created: {xlsx_file}")

# ============================================================
# 3. CREATE JSON (Update Email)
# ============================================================
json_file = os.path.join(current_dir, "email_update.json")
email_data = {
    "from": "billing@puremilk.com",
    "to": "procurement@sohamsweets.com",
    "subject": "URGENT: Pricing and Delivery Updates for Q2",
    "date": "2026-04-03T10:30:00",
    "body": "Hello team, due to fuel price hikes, the price of Premium Mawa is increasing to $55.00 per kg. Delivery times are now 21 business days. The 12-month quality guarantee remains unchanged."
}

with open(json_file, 'w') as f:
    json.dump(email_data, f, indent=4)

print(f"✅ Created: {json_file}")
print("\n🚀 ALL DEMO FILES ARE READY IN YOUR PROJECT FOLDER!")