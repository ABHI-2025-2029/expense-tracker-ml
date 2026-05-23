from flask import Flask, request, jsonify, render_template
from sklearn.linear_model import LinearRegression
import numpy as np
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# -------------------------------
# DATABASE FUNCTIONS
# -------------------------------
def predict_next_expense():
    expenses = get_expenses()

    if len(expenses) < 2:
        return "Not enough data"

    # X = days (1,2,3...)
    X = []
    y = []

    for i, exp in enumerate(expenses):
        X.append([i])   # day index
        y.append(exp["amount"])

    X = np.array(X)
    y = np.array(y)

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next day
    next_day = np.array([[len(expenses)]])
    prediction = model.predict(next_day)

    return round(prediction[0], 2)
def get_db_connection():
    conn = sqlite3.connect('expenses.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER,
            category TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()


def add_expense(amount, category, date):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO expenses (amount, category, date) VALUES (?, ?, ?)",
        (amount, category, date)
    )
    conn.commit()
    conn.close()


def get_expenses():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM expenses").fetchall()
    conn.close()

    # convert to dictionary list
    expenses = []
    for row in rows:
        expenses.append({
            "id": row["id"],
            "amount": row["amount"],
            "category": row["category"],
            "date": row["date"]
        })

    return expenses


# -------------------------------
# ROUTES
# -------------------------------
@app.route('/predict')
def predict():
    result = predict_next_expense()

    return {
        "prediction": result
    }
@app.route('/')
def home():
    return render_template('index.html')


# ADD EXPENSE
@app.route('/expense', methods=['POST'])
def add_expense_route():
    data = request.get_json()

    if not data:
        return {"error": "No data provided"}, 400

    if 'amount' not in data or 'category' not in data or 'date' not in data:
        return {"error": "Missing fields"}, 400

    try:
        amount = int(data['amount'])
    except:
        return {"error": "Amount must be a number"}, 400

    category = data['category']
    date = data['date']

    add_expense(amount, category, date)

    return {"message": "Expense added successfully"}


# GET ALL EXPENSES
@app.route('/expense', methods=['GET'])
def get_all_expenses():
    expenses = get_expenses()
    return {"expenses": expenses}


# SUMMARY
@app.route('/summary')
def get_summary():
    expenses = get_expenses()

    total = 0
    category_data = {}

    for exp in expenses:
        amount = exp["amount"]
        category = exp["category"]

        total += amount

        if category in category_data:
            category_data[category] += amount
        else:
            category_data[category] = amount

    return {
        "total": total,
        "category_data": category_data
    }

@app.route('/test')
def test_data():
    add_expense(200, "Food", "2026-04-10")
    add_expense(500, "Travel", "2026-04-10")
    add_expense(1000, "Shopping", "2026-04-10")

    return {"message": "Test data added"}
# INSIGHTS
@app.route('/insights')
def get_insights():
    expenses = get_expenses()

    category_data = {}

    for exp in expenses:
        amount = exp["amount"]
        category = exp["category"]

        if category in category_data:
            category_data[category] += amount
        else:
            category_data[category] = amount

    if not category_data:
        return {"message": "No data available"}

    top_category = max(category_data, key=category_data.get)

    return {
        "message": f"You are spending most on {top_category}"
    }


# -------------------------------
# RUN APP
# -------------------------------

if __name__ == "__main__":
    create_table()
    app.run(debug=True)