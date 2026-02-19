from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file,flash
from ai_forecast import profit_forecast
import csv, os
from datetime import datetime
from datetime import date
from collections import defaultdict
from openai import OpenAI
import os
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI
import random
import jwt
from functools import wraps


load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
JWT_ALGORITHM = "HS256"

def generate_jwt_token(username, role):
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow().timestamp() + (60 * 60 * 2)  # 2 hours expiry
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        token = token.replace("Bearer ", "")
        decoded = verify_jwt_token(token)

        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        return func(*args, **kwargs)

    return wrapper


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")




app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "True") == "True",
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER")
)

mail = Mail(app)

USERS_FILE = "users.csv"
SALES_FILE = "sales.csv"
INVENTORY_FILE = "inventory.csv"


# ---------- CSV Helpers ----------
def read_csv(file):
    if not os.path.exists(file):
        return []
    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv_new(file, fields, rows):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)



def read_csv_template(file):
    if not os.path.exists(file):
        return []

    with open(file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
    
def write_csv_template(file, fieldnames, rows):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)



def write_csv(file, fields, rows):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def write_csv_register(file, fields, rows):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def login_required(role=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login"))
            if role and session["role"] not in role:
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator








# ===================== LOGIN =====================
@app.route("/", methods=["GET", "POST"])
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = read_csv(USERS_FILE)
        for u in users:
            if u["username"] == request.form["username"] and u["password"] == request.form["password"]:
                session["username"] = u["username"]
                session["role"] = u["role"]
                token = generate_jwt_token(u["username"], u["role"])
                session["jwt_token"] = token

                if u["role"] == "owner":
                    return redirect(url_for("owner_dashboard"))
                elif u["role"] == "accountant":
                    return redirect(url_for("accountant_dashboard"))
                elif u["role"] == "staff":
                    return redirect(url_for("staff_dashboard"))
                else:
                    return redirect(url_for("owner_dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/get-token")
@login_required(["owner", "accountant", "staff"])
def get_token():
    return jsonify({
        "username": session["username"],
        "role": session["role"],
        "jwt_token": session.get("jwt_token")
    })

@app.route("/secure-api")
@jwt_required
def secure_api():
    return jsonify({"message": "This is protected by JWT"})



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = read_csv(USERS_FILE)

        user = {
            "username": request.form.get("username"),
            "password": request.form.get("password"),
            "role": request.form.get("role")
        }  # full_name is ignored here ✅

        users.append(user)

        write_csv_register(USERS_FILE, ["username", "password", "role"], users)
        return redirect(url_for("login"))

    return render_template("register.html")





# ---------- Dashboards ----------
@app.route("/owner")
@login_required(["owner"])
def owner_dashboard():
    sales = read_csv(SALES_FILE)

    income = sum(float(s["transaction_amount"]) for s in sales if s["transaction_type"] == "Income")
    expense = sum(float(s["transaction_amount"]) for s in sales if s["transaction_type"] == "Expense")

    return render_template(
        "owner_dashboard.html",
        sales=sales,
        income=income,
        expense=expense,
        profit=income - expense
    )


@app.route("/ai-forecast")
@login_required(["owner"])
def ai_forecast():
    forecast = profit_forecast(SALES_FILE, days=7)

    suggestions = []

    avg_profit = sum(forecast["profits"]) / len(forecast["profits"])

    if avg_profit > 0:
        suggestions.append("📈 AI predicts increasing profit trend. Consider expanding promotions.")
    else:
        suggestions.append("⚠️ AI detects possible losses. Reduce operational expenses.")

    if max(forecast["profits"]) > avg_profit * 1.5:
        suggestions.append("🔥 Peak profit days expected — increase stock & staff.")

    return jsonify({
        "forecast": forecast,
        "suggestions": suggestions
    })
from ai_forecast import (
    monthly_income_expense_forecast,
    yearly_income_expense_forecast
)

@app.route("/ai-forecast-advanced")
@login_required(["owner"])
def ai_forecast_advanced():
    monthly = monthly_income_expense_forecast(SALES_FILE)
    yearly = yearly_income_expense_forecast(SALES_FILE)

    suggestions = []

    if sum(monthly["income"]) > sum(monthly["expense"]):
        suggestions.append("📈 Monthly profits look healthy. Consider reinvesting.")
    else:
        suggestions.append("⚠️ Monthly expenses may overtake income. Review costs.")

    if yearly["income"][-1] > yearly["income"][0]:
        suggestions.append("🚀 Long-term revenue growth expected.")
    else:
        suggestions.append("🛑 Revenue growth slowing. Improve marketing strategy.")

    return jsonify({
        "monthly": monthly,
        "yearly": yearly,
        "suggestions": suggestions
    })




@app.route("/staff")
@login_required(["staff"])
def staff_dashboard():
    sales = read_csv(SALES_FILE)
    today = datetime.now().strftime("%Y-%m-%d")

    today_income = [
        s for s in sales
        if s["date"] == today and s["transaction_type"] == "Income"
    ]

    today_expense = [
        s for s in sales
        if s["date"] == today and s["transaction_type"] == "Expense"
    ]

    total_income = sum(float(s["transaction_amount"]) for s in today_income)
    total_expense = sum(float(s["transaction_amount"]) for s in today_expense)

    return render_template(
        "staff_dashboard.html",
        total_amount=round(total_income, 2),
        total_orders=len(today_income),
        net_collection=round(total_income - total_expense, 2)
    )



@app.route("/api/staff/today-sales")
@login_required(["staff"])
def staff_today_sales_api():
    sales = read_csv(SALES_FILE)

    today_str = datetime.now().strftime("%Y-%m-%d")

    item_sales = defaultdict(float)

    for s in sales:
        if s["date"] == today_str and s["transaction_type"] == "Income":
            item_sales[s["item_name"]] += float(s["transaction_amount"])

    return jsonify({
        "labels": list(item_sales.keys()),
        "data": list(item_sales.values())
    })


@app.route("/staff/items-today")
@login_required(["staff"])
def items_sold_today():
    sales = read_csv(SALES_FILE)
    today = date.today().strftime("%Y-%m-%d")

    items = defaultdict(int)
    for s in sales:
        if s["date"] == today and s["transaction_type"] == "Income":
            items[s["item_name"]] += int(s["quantity"])

    return render_template("staff_items_today.html", items=items, today=today)
from flask import render_template, request, redirect, url_for, flash
import csv

INVENTORY_FILE = "inventory.csv"


def read_csv(file):
    with open(file, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(file, data):
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

@app.route("/staff/take-order", methods=["GET", "POST"])
@login_required(["staff"])
def staff_take_order():

    inventory = read_csv(INVENTORY_FILE)

    # 🔹 Build item dictionary for UI (menu grid)
    items = {}
    for i in inventory:
        items[i["item_name"]] = {
            "category": i.get("item_type", "General"),
            "price": float(i.get("price", 0)),
            "stock": int(i.get("stock", 0))
        }

    # ===============================
    # 🔹 POST: Place Order
    # ===============================
    if request.method == "POST":

        orders = request.form.getlist("item_name[]")
        quantities = request.form.getlist("quantity[]")

        for name, qty in zip(orders, quantities):

            if not name:
                continue

            qty = int(qty)

            if qty <= 0:
                continue

            for item in inventory:

                if item["item_name"] == name:

                    current_stock = int(item.get("stock", 0))

                    # ✅ Prevent negative stock
                    if qty > current_stock:
                        qty = current_stock

                    item["stock"] = str(current_stock - qty)
                    break

        # 🔹 Save updated inventory
        write_csv(INVENTORY_FILE, inventory)

        flash("Order placed and inventory updated!", "success")

        return redirect(url_for("staff_take_order"))

    # ===============================
    # 🔹 GET: Show Menu
    # ===============================
    return render_template(
        "staff_take_order.html",
        items=items
    )

# ================= LOW STOCK MAIL =================

OWNER_EMAIL = os.getenv("ALERT_RECIPIENT", "admin@example.com")
ACCOUNTANT_EMAIL = os.getenv("ALERT_RECIPIENT", "admin@example.com")

def send_low_stock_alert():
    with app.app_context():
        items = read_csv(INVENTORY_FILE)

        low_stock_items = [
            item for item in items
            if int(item["stock"]) < 5
        ]

        if not low_stock_items:
            return

        # ================= PDF GENERATION =================
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_filename = "low_stock_alert.pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_filename)

        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4

        y = height - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "LOW STOCK ALERT REPORT")
        y -= 30

        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Restaurant: FlavorFusion Restaurant")
        y -= 15
        c.drawString(50, y, f"Generated on: {timestamp}")
        y -= 30

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Item Name")
        c.drawString(200, y, "Remaining Stock")
        c.drawString(350, y, "Price")
        y -= 15

        c.line(50, y, 550, y)
        y -= 20

        c.setFont("Helvetica", 10)

        for item in low_stock_items:
            c.drawString(50, y, item["item_name"])
            c.drawString(200, y, item["stock"])
            c.drawString(350, y, item["price"])
            y -= 18

            if y < 50:  # new page safety
                c.showPage()
                y = height - 50

        y -= 30
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(
            50,
            y,
            "Please restock the above items immediately to avoid service disruption."
        )

        c.save()
        # ===================================================

        # ================= EMAIL BODY =================
        email_body = f"""
Dear Management Team,

This is an automated stock monitoring alert from FlavorFusion Restaurant.

One or more inventory items have fallen below the minimum stock threshold (less than 5 units).

Please find the attached PDF report containing:
- Item Name
- Remaining Stock
- Price details

Immediate action is recommended to ensure uninterrupted restaurant operations.

This is a system-generated message.
Do not reply to this email.

Regards,
Inventory Management System
FlavorFusion Restaurant
"""
        # ==============================================

        msg = Message(
            subject="🚨 Low Stock Alert – Immediate Attention Required",
            recipients=[OWNER_EMAIL, ACCOUNTANT_EMAIL],
            body=email_body
        )

        msg.attach(
            filename="Low_Stock_Report.pdf",
            content_type="application/pdf",
            data=open(pdf_path, "rb").read()
        )

        mail.send(msg)

@app.route("/send-management-report")
@login_required(["owner"])
def send_management_report_route():
    try:
        generate_and_send_combined_report()
        flash("Management report sent successfully!", "success")
    except Exception as e:
        print(f"Error sending report: {e}")
        flash(f"Failed to send report: {str(e)}", "danger")
    return redirect(url_for("owner_dashboard"))

def generate_and_send_combined_report():
    with app.app_context():
        # 1. Gather Data
        inventory = read_csv(INVENTORY_FILE)
        sales = read_csv(SALES_FILE)
        
        low_stock_items = [i for i in inventory if int(i.get("stock", 0)) < 5]
        
        income = sum(float(s["transaction_amount"]) for s in sales if s["transaction_type"] == "Income")
        expense = sum(float(s["transaction_amount"]) for s in sales if s["transaction_type"] == "Expense")
        profit = income - expense
        
        # 2. Generate PDF
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_filename = "management_report.pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_filename)
        
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 50
        
        # Title
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, y, "RESTAURANT MANAGEMENT REPORT")
        y -= 30
        
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Generated on: {timestamp}")
        y -= 40
        
        # Financial Overview
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Financial Overview")
        y -= 25
        
        c.setFont("Helvetica", 12)
        c.drawString(70, y, f"Total Revenue: ₹{income:,.2f}")
        y -= 20
        c.drawString(70, y, f"Total Expense: ₹{expense:,.2f}")
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y, f"Net Profit: ₹{profit:,.2f}")
        y -= 40
        
        # Low Stock Alert Section
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Low Stock Alert")
        y -= 25
        
        if not low_stock_items:
            c.setFont("Helvetica-Oblique", 11)
            c.drawString(70, y, "No items are currently low on stock.")
            y -= 20
        else:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "Item Name")
            c.drawString(250, y, "Remaining")
            c.drawString(400, y, "Price")
            y -= 15
            c.line(50, y, 550, y)
            y -= 20
            
            c.setFont("Helvetica", 11)
            for item in low_stock_items:
                if y < 80:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, item["item_name"])
                c.drawString(250, y, item["stock"])
                c.drawString(400, y, f"₹{float(item['price']):,.2f}")
                y -= 20
                
        c.save()
        
        # 3. Send Email
        dashboard_url = url_for('owner_dashboard', _external=True)
        html_body = render_template(
            "management_email.html",
            income=income,
            expense=expense,
            profit=profit,
            low_stock_items=low_stock_items,
            dashboard_url=dashboard_url
        )

        msg = Message(
            subject=f"Restaurant Management Report - {datetime.now().strftime('%Y-%m-%d')}",
            recipients=[OWNER_EMAIL],
            html=html_body
        )
        
        with open(pdf_path, "rb") as f:
            msg.attach(
                filename="Management_Report.pdf",
                content_type="application/pdf",
                data=f.read()
            )
            
        mail.send(msg)



# ===================================================
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    send_low_stock_alert,
    trigger="interval",
    seconds=3600  # 🔥 sends every 10 seconds
)

scheduler.start()




@app.route("/staff/menu")
@login_required(["staff"])
def staff_menu():
    items = read_csv(INVENTORY_FILE)
    return render_template("staff_menu.html", items=items)



@app.route("/add_transaction", methods=["POST"])
@login_required(["owner"])
def add_transaction():
    sales = read_csv(SALES_FILE)
    inventory = read_csv(INVENTORY_FILE)

    LOW_STOCK_LIMIT = 5

    item_name = request.form["item_name"]
    quantity = int(request.form["quantity"])
    transaction_type = request.form["transaction_type"]

    # Only get expense data if Expense selected
    expense_category = request.form.get("expense_category", "")
    expense_amount_raw = request.form.get("expense_amount", "")

    # ✅ Prevent float("") error
    expense_amount = float(expense_amount_raw) if expense_amount_raw.strip() != "" else 0

    # -------- LOW STOCK CHECK --------
    item = None
    with open('inventory.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['item_name'].strip().lower() == item_name.strip().lower():
                item = row
                break

    if item:
        stock = int(item['stock'])
        if stock <= LOW_STOCK_LIMIT:
            flash(f"⚠️ Warning: Stock for '{item_name}' is low ({stock} left).")

    # -------- PRICE CALCULATION --------
    item_price = 0

    for i in inventory:
        if i["item_name"] == item_name:
            item_price = float(i["price"])

            if transaction_type == "Income":
                i["stock"] = str(int(i["stock"]) - quantity)

    # ✅ Keep your old correct logic
    if transaction_type == "Income":
        transaction_amount = item_price * quantity
    else:
        transaction_amount = expense_amount

    order_id = len(sales) + 1
    time_now = datetime.now()

    new = {
        "order_id": order_id,
        "date": request.form["date"],
        "item_name": item_name,
        "item_type": request.form["item_type"],
        "item_price": item_price if transaction_type == "Income" else expense_amount,
        "quantity": quantity,
        "transaction_amount": transaction_amount,
        "transaction_type": transaction_type,
        "expense_category": expense_category if transaction_type == "Expense" else "",
        "received_by": session["username"],
        "time_of_sale": time_now.strftime("%H:%M:%S")
    }

    sales.append(new)

    write_csv(SALES_FILE, sales)
    write_csv(INVENTORY_FILE, inventory)

    return redirect(url_for("receipt", oid=order_id))


# ---------- User Management ----------
@app.route("/users")
@login_required(["owner"])
def users():
    users = read_csv(USERS_FILE)
    return render_template("users.html", users=users)


@app.route("/edit_user/<username>", methods=["POST"])
@login_required(["owner"])
def edit_user(username):
    users = read_csv(USERS_FILE)

    for u in users:
        if u["username"] == username:
            u["role"] = request.form["role"]

    write_csv_new(USERS_FILE, users[0].keys(), users)
    return redirect(url_for("users"))


@app.route("/delete_user/<username>")
@login_required(["owner"])
def delete_user(username):
    users = read_csv(USERS_FILE)

    users = [u for u in users if u["username"] != username]

    write_csv_new(USERS_FILE, users[0].keys(), users)
    return redirect(url_for("users"))


# ---------- Edit Transaction ----------
@app.route("/edit/<int:oid>", methods=["GET", "POST"])
@login_required(["owner"])
def edit_transaction(oid):
    sales = read_csv(SALES_FILE)

    if oid < 1 or oid > len(sales):
        return "Transaction not found", 404

    tx = sales[oid - 1]

    if request.method == "POST":
        tx["date"] = request.form["date"]
        tx["item_name"] = request.form["item_name"]
        tx["item_type"] = request.form["item_type"]
        tx["item_price"] = request.form["item_price"]
        tx["quantity"] = request.form["quantity"]
        tx["transaction_amount"] = request.form["transaction_amount"]
        tx["transaction_type"] = request.form["transaction_type"]

        write_csv_new(SALES_FILE, sales[0].keys(), sales)
        return redirect(url_for("all_transactions"))

    return render_template("edit_transaction.html", tx=tx)


# ---------- Delete Transaction ----------
@app.route("/delete/<int:oid>")
@login_required(["owner"])
def delete_transaction(oid):
    sales = read_csv(SALES_FILE)

    if oid < 1 or oid > len(sales):
        return redirect(url_for("all_transactions"))

    sales.pop(oid - 1)

    for i, s in enumerate(sales):
        s["order_id"] = i + 1

    write_csv_new(SALES_FILE, sales[0].keys(), sales)
    return redirect(url_for("all_transactions"))

# ---------- Inventory ----------
@app.route("/inventory")
@login_required(["owner"])
def inventory():
    items = read_csv(INVENTORY_FILE)
    return render_template("inventory.html", items=items)


@app.route("/update_inventory/<item_name>", methods=["POST"])
@login_required(["owner"])
def update_inventory(item_name):
    inventory = read_csv(INVENTORY_FILE)

    for item in inventory:
        if item["item_name"] == item_name:
            item["stock"] = request.form["stock"]
            item["price"] = request.form["price"]

    write_csv_new(INVENTORY_FILE, inventory[0].keys(), inventory)
    return redirect(url_for("inventory"))

#------Receipt-------
@app.route("/receipt/<int:oid>")
@login_required(["owner"])
def receipt(oid):
    sales = read_csv(SALES_FILE)

    if oid < 1 or oid > len(sales):
        return "Receipt not found", 404

    tx = sales[oid - 1]

    # Get template style from URL (default = classic)
    template_style = request.args.get("style", "classic")

    return render_template(
        "receipt.html",
        tx=tx,
        template_style=template_style
    )



# ---------- Chart Data ----------
from collections import defaultdict

@app.route("/chart-data")
@login_required(["owner", "accountant"])
def chart_data():
    sales = read_csv(SALES_FILE)

    daily_profit = defaultdict(float)
    monthly_profit = defaultdict(float)
    yearly_profit = defaultdict(float)

    daily_revenue = defaultdict(float)   # ✅ NEW
    daily_expense = defaultdict(float)   # ✅ NEW

    expense_categories = defaultdict(float)

    for s in sales:
        date = s["date"]
        year = date[:4]
        month = date[:7]
        amount = float(s["transaction_amount"])

        if s["transaction_type"] == "Income":
            # ----- PROFIT -----
            daily_profit[date] += amount
            monthly_profit[month] += amount
            yearly_profit[year] += amount

            # ----- REVENUE -----
            daily_revenue[date] += amount

        else:
            # ----- PROFIT -----
            daily_profit[date] -= amount
            monthly_profit[month] -= amount
            yearly_profit[year] -= amount

            # ----- EXPENSE -----
            daily_expense[date] += amount

            category = s.get("expense_category", "Other") or "Other"
            expense_categories[category] += amount

    return jsonify({
        "daily_profit": dict(daily_profit),
        "monthly_profit": dict(monthly_profit),
        "yearly_profit": dict(yearly_profit),
        "expense_categories": dict(expense_categories),

        # ✅ NEW DATA FOR REVENUE vs EXPENSES
        "daily_revenue": dict(daily_revenue),
        "daily_expense": dict(daily_expense)
    })

@app.route("/staff/chart-data")
@login_required(["staff"])
def staff_chart_data():
    sales = read_csv(SALES_FILE)

    expense_categories = defaultdict(float)
    today_sales = defaultdict(int)

    today = datetime.now().strftime("%Y-%m-%d")

    for s in sales:
        amount = float(s["transaction_amount"])

        # Expense category pie
        if s["transaction_type"] == "Expense":
            category = s.get("expense_category", "Other") or "Other"
            expense_categories[category] += amount

        # Today's sales bar chart
        if s["transaction_type"] == "Income" and s["date"] == today:
            today_sales[s["item_name"]] += int(s["quantity"])

    return jsonify({
        "expense_categories": dict(expense_categories),
        "today_sales": dict(today_sales)
    })
#----------------------
@app.route("/accountant")
@login_required(["accountant"])
def accountant_dashboard():
    sales = read_csv(SALES_FILE)
    inventory = read_csv(INVENTORY_FILE)

    today = datetime.now().strftime("%Y-%m-%d")

    today_sales = sum(
        float(s["transaction_amount"])
        for s in sales
        if s["transaction_type"] == "Income" and s["date"] == today
    )

    today_expense = sum(
        float(s["transaction_amount"])
        for s in sales
        if s["transaction_type"] == "Expense" and s["date"] == today
    )

    total_sales = sum(
        float(s["transaction_amount"])
        for s in sales
        if s["transaction_type"] == "Income"
    )

    return render_template(
        "accountant_dashboard.html",
        sales=sales,
        inventory=inventory,
        today_sales=round(today_sales, 2),
        today_expense=round(today_expense, 2),
        total_sales=round(total_sales, 2)
    )

@app.route("/accountant/add-product", methods=["POST"])
@login_required(["accountant"])
def accountant_add_product():
    inventory = read_csv(INVENTORY_FILE)

    item_name = request.form["item_name"]
    category = request.form["category"]
    price = request.form["price"]

    inventory.append({
        "item_name": item_name,
       
        "price": price,
        "stock": 0
    })

    fieldnames = inventory[0].keys() if inventory else []
    write_csv_new(INVENTORY_FILE, fieldnames, inventory)

    flash(f"Product '{item_name}' added successfully", "success")
    return redirect("/accountant")


@app.route("/accountant/edit-price/<item_name>", methods=["POST"])
@login_required(["accountant"])
def accountant_edit_price(item_name):
    inventory = read_csv(INVENTORY_FILE)
    new_price = request.form["price"]

    for item in inventory:
        if item["item_name"] == item_name:
            item["price"] = new_price
            break

    fieldnames = inventory[0].keys() if inventory else []
    write_csv_new(INVENTORY_FILE, fieldnames, inventory)

    flash(f"Price updated successfully for {item_name}", "success")
    return redirect("/accountant")


@app.route("/accountant/export")
@login_required(["accountant"])
def export_accountant_report():
    return send_file(SALES_FILE, as_attachment=True)
@app.route("/accountant/view-table")
@login_required(["accountant"])
def accountant_view_table():
    sales = read_csv(SALES_FILE)
    return render_template("accountant_view_table.html", sales=sales)

@app.context_processor
def inject_accountant_snapshot():
    if "role" not in session or session.get("role") != "accountant":
        return {}

    sales = read_csv(SALES_FILE)
    today = datetime.now().strftime("%Y-%m-%d")

    today_sales = sum(
        float(s["transaction_amount"])
        for s in sales
        if s["transaction_type"] == "Income" and s["date"] == today
    )

    today_expense = sum(
        float(s["transaction_amount"])
        for s in sales
        if s["transaction_type"] == "Expense" and s["date"] == today
    )

    return dict(
        today_sales=round(today_sales, 2),
        today_expense=round(today_expense, 2)
    )
@app.route("/accountant/edit-transaction/<order_id>", methods=["POST"])
@login_required(["accountant"])
def accountant_edit_transaction(order_id):
    sales = read_csv(SALES_FILE)

    for s in sales:
        if s["order_id"] == order_id:
            s["item_name"] = request.form["item_name"]
            s["item_type"] = request.form["item_type"]
            s["transaction_amount"] = request.form["transaction_amount"]
            s["expense_category"] = request.form.get("expense_category", "")

    write_csv_new(SALES_FILE, sales)
    return redirect(url_for("accountant_view_table"))

@app.route("/accountant/edit/<int:order_id>", methods=["GET", "POST"])
@login_required(["accountant"])
def accountant_edit_page(order_id):
    sales = read_csv(SALES_FILE)

    transaction = None
    for s in sales:
        if int(s["order_id"]) == order_id:
            transaction = s
            break

    if not transaction:
        flash("Transaction not found", "danger")
        return redirect("/accountant/view-table")

    if request.method == "POST":
        transaction["item_name"] = request.form["item_name"]
        transaction["item_type"] = request.form["item_type"]
        transaction["transaction_amount"] = request.form["transaction_amount"]

        if transaction["transaction_type"] == "Expense":
            transaction["expense_category"] = request.form.get("expense_category", "")

        # ✅ THIS IS THE FIX
        fieldnames = sales[0].keys() if sales else []
        write_csv_new(SALES_FILE, fieldnames, sales)

        flash("Transaction updated successfully", "success")
        return redirect("/accountant/view-table")

    return render_template(
        "accountant_edit_transaction.html",
        s=transaction
    )

# ================= SCHEDULER =================

# ============================================
TEMPLATE_FILE = "template_settings.csv"

@app.route("/templates", methods=["GET", "POST"])
@login_required(["owner"])
def templates():
    if request.method == "POST":
        selected = request.form["template"]

        write_csv_template(
            TEMPLATE_FILE,
            ["template"],
            [{"template": selected}]
        )

        flash("Template updated successfully!", "success")

    current = read_csv_template(TEMPLATE_FILE)
    selected_template = current[0]["template"] if current else "classic"

    return render_template("templates.html", selected_template=selected_template)


@app.route("/ai-analysis")
@login_required(["owner"])
def ai_analysis():
    sales = read_csv(SALES_FILE)

    monthly_data = defaultdict(lambda: {"revenue": 0, "expense": 0})

    # Collect monthly revenue & expense
    for s in sales:
        month = s["date"][:7]  # YYYY-MM
        amount = float(s["transaction_amount"])

        if s["transaction_type"] == "Income":
            monthly_data[month]["revenue"] += amount
        else:
            monthly_data[month]["expense"] += amount

    months = sorted(monthly_data.keys())

    monthly_labels = months
    monthly_revenue = []
    monthly_expense = []
    monthly_profit = []

    for m in months:
        revenue = monthly_data[m]["revenue"]
        expense = monthly_data[m]["expense"]

        # AI growth simulation
        predicted_revenue = round(revenue * 1.10, 2)
        predicted_expense = round(expense * 1.07, 2)
        predicted_profit = round(predicted_revenue - predicted_expense, 2)

        monthly_revenue.append(predicted_revenue)
        monthly_expense.append(predicted_expense)
        monthly_profit.append(predicted_profit)

    # Monthly totals prediction (latest month basis)
    if monthly_profit:
        predicted_revenue_total = monthly_revenue[-1]
        predicted_expense_total = monthly_expense[-1]
        predicted_profit_total = monthly_profit[-1]
    else:
        predicted_revenue_total = 0
        predicted_expense_total = 0
        predicted_profit_total = 0

    # Yearly prediction
    current_year = datetime.now().year
    yearly_labels = [str(current_year + i) for i in range(3)]

    yearly_profit = []
    base_profit = predicted_profit_total

    for i in range(3):
        growth = 1 + (0.12 * i)
        yearly_profit.append(round(base_profit * growth * 12, 2))

    # Weekly forecast (Next 7 Days)
    weekly_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    avg_daily_profit = predicted_profit_total / 30 if predicted_profit_total else 0

    weekly_profit = [
        round(avg_daily_profit * (1 + random.uniform(0.01, 0.10)), 2)
        for _ in range(7)
    ]

    # AI Suggestions Logic
    ai_suggestions = []

    if predicted_profit_total > 100000:
        ai_suggestions.append("📈 Monthly profits look healthy. Consider reinvesting into expansion.")
    elif predicted_profit_total > 50000:
        ai_suggestions.append("💡 Stable growth detected. Focus on marketing for faster expansion.")
    else:
        ai_suggestions.append("🛑 Revenue growth slowing. Improve marketing strategy.")

    if predicted_expense_total > predicted_revenue_total * 0.7:
        ai_suggestions.append("⚠️ Expenses are high. Consider cost optimization.")
    else:
        ai_suggestions.append("✅ Expense control looks healthy.")

    return render_template(
        "ai_analysis.html",
        monthly_labels=monthly_labels,
        monthly_revenue=monthly_revenue,
        monthly_expense=monthly_expense,
        monthly_profit=monthly_profit,
        yearly_labels=yearly_labels,
        yearly_profit=yearly_profit,
        weekly_labels=weekly_labels,
        weekly_profit=weekly_profit,
        predicted_revenue=predicted_revenue_total,
        predicted_expense=predicted_expense_total,
        predicted_profit=predicted_profit_total,
        ai_suggestions=ai_suggestions
    )

@app.route("/add_transaction_page")
@login_required(["owner"])
def add_transaction_page():
    """Render the add transaction page"""
    from datetime import datetime
    now = datetime.now()
    return render_template("add_transaction.html", now=now)

@app.route("/all_transactions")
@login_required(["owner", "accountant"])
def all_transactions():
    sales = read_csv(SALES_FILE)

    # ✅ Convert numeric fields properly
    for s in sales:
        s["transaction_amount"] = float(s.get("transaction_amount", 0) or 0)
        s["quantity"] = int(s.get("quantity", 0) or 0)

    return render_template("all_transactions.html", sales=sales)


@app.route("/accountant/add-product-page")
@login_required(["accountant"])
def add_product_page():
    """Render the add product page"""
    inventory = read_csv(INVENTORY_FILE)
    # Get recent products (last 5 added)
    recent_products = inventory[-5:] if inventory else []
    return render_template("add_product.html", recent_products=recent_products)





if __name__ == "__main__":
    app.run(debug=False)
