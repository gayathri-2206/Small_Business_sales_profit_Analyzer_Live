import csv
import random
from datetime import datetime, timedelta
from collections import defaultdict

# ================= CONFIG =================
OUTPUT_FILE = "sales.csv"
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime.now()          # 2026 till today
TOTAL_RECORDS = 5000               # change to 1000 if needed

# ================= ITEMS =================
income_items = [
    ("Burger", "Food", 120),
    ("Pizza", "Food", 250),
    ("Pasta", "Food", 220),
    ("Coffee", "Beverage", 80),
    ("Tea", "Beverage", 40),
    ("Cold Drink", "Beverage", 60),
    ("Sandwich", "Food", 150)
]

expense_items = [
    ("Vegetables", "Grocery", "Vegetables & Groceries"),
    ("Gas Cylinder", "Utility", "Gas / Fuel"),
    ("Detergent", "Other", "Cleaning Supplies"),
    ("Oil", "Raw", "Raw Materials"),
    ("Repair Work", "Service", "Minor Repairs")
]

# ================= CSV HEADER =================
header = [
    "order_id",
    "date",
    "item_name",
    "item_type",
    "item_price",
    "quantity",
    "transaction_amount",
    "transaction_type",
    "expense_category",
    "received_by",
    "time_of_sale"
]

# ================= DATE RANGE =================
dates = []
current = START_DATE
while current <= END_DATE:
    dates.append(current)
    current += timedelta(days=1)

# ================= GENERATION =================
rows = []
order_id = 1001

for _ in range(TOTAL_RECORDS):
    date = random.choice(dates)
    date_str = date.strftime("%Y-%m-%d")
    time_str = f"{random.randint(9,22)}:{random.randint(0,59):02d}"

    # PROFIT LOGIC: 80% income, 20% expense
    if random.random() < 0.8:
        item, item_type, price = random.choice(income_items)
        qty = random.randint(1, 5)
        amount = price * qty

        row = [
            order_id,
            date_str,
            item,
            item_type,
            price,
            qty,
            amount,
            "Income",
            "",
            "staff",
            time_str
        ]
    else:
        item, item_type, category = random.choice(expense_items)
        amount = random.randint(200, 1200)

        row = [
            order_id,
            date_str,
            item,
            item_type,
            0,
            1,
            amount,
            "Expense",
            category,
            "owner",
            time_str
        ]

    rows.append(row)
    order_id += 1

# ================= WRITE CSV =================
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print("======================================")
print("✅ sales.csv generated successfully")
print(f"📅 Date Range: {START_DATE.date()} → {END_DATE.date()}")
print(f"📊 Records: {TOTAL_RECORDS}")
print("💰 Profit guaranteed (Income > Expense)")
print("======================================")
