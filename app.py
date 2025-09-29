import os
os.system("mysql -u flaskuser -prishisuren < init.sql")
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# ------------------ DB Config ------------------
db_config = {
    "host": "localhost",
    "user": "flaskuser",       # change to your user
    "password": "rishisuren",   # change to your password
    "database": "feedback_system"
}

def get_db():
    return mysql.connector.connect(**db_config)

# ------------------ Helper Functions ------------------
def get_user_by_email(email):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def current_user():
    if "user_id" in session:
        return {"id": session["user_id"], "name": session["name"], "role": session["role"]}
    return None

# ------------------ Routes ------------------


@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only admins can add products.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        vendor_id = request.form["vendor_id"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Products (name, description, vendor_id, created_at) VALUES (%s, %s, %s, NOW())",
            (name, description, vendor_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Product added successfully!", "success")
        return redirect(url_for("home"))

    # Get vendor list for dropdown
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM Vendors")
    vendors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("add_product.html", user=user, vendors=vendors)


@app.route("/products")
def products():
    user = current_user()
    if not user or user["role"] != "customer":
        flash("You must be logged in as a customer to view products.", "danger")
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Fetch all products with vendor names
    cursor.execute("""
        SELECT p.id, p.name, p.description, v.name AS vendor_name
        FROM Products p
        LEFT JOIN Vendors v ON p.vendor_id = v.id
    """)
    products_list = cursor.fetchall()

    # Fetch all feedback submitted by this user
    cursor.execute("""
        SELECT f.id AS feedback_id, f.comment AS feedback, f.rating, p.name AS product_name, v.name AS vendor_name
        FROM Feedback f
        JOIN Products p ON f.product_id = p.id
        LEFT JOIN Vendors v ON p.vendor_id = v.id
        WHERE f.user_id = %s
        ORDER BY f.submitted_at DESC
    """, (user["id"],))
    my_feedbacks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("products.html", products=products_list, my_feedbacks=my_feedbacks, user=user)




@app.route("/")
def home():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if user["role"] == "admin":
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Fetch all feedbacks with product names
        cursor.execute("""
            SELECT f.id AS feedback_id, f.comment, f.rating, p.name AS product_name
            FROM Feedback f
            JOIN Products p ON f.product_id = p.id
        """)
        feedbacks = cursor.fetchall()

        # Fetch replies for mapping feedback_id -> reply_text
        cursor.execute("SELECT feedback_id, reply_text FROM Review_Replies")
        replies = cursor.fetchall()
        reply_map = {r["feedback_id"]: r["reply_text"] for r in replies}

        # Fetch products without feedback
        cursor.execute("""
            SELECT pr.id, pr.name, pr.description, v.name AS vendor_name
            FROM Products pr
            JOIN Vendors v ON pr.vendor_id = v.id
            WHERE pr.id NOT IN (SELECT DISTINCT product_id FROM Feedback)
        """)
        products_no_feedback = cursor.fetchall()


        cursor.close()
        conn.close()

        return render_template("admin_dashboard.html",
                               user=user,
                               feedbacks=feedbacks,
                               reply_map=reply_map,
                               products_no_feedback=products_no_feedback)

    else:
        # customer flow
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.id, p.name, p.description, v.name AS vendor_name
            FROM Products p
            LEFT JOIN Vendors v ON p.vendor_id = v.id
        """)
        products_list = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("products.html", products=products_list, user=user)




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        user = get_user_by_email(email)
        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome {user['name']}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/feedback/<int:product_id>", methods=["GET", "POST"])
def feedback(product_id):
    user = current_user()
    if not user or user["role"] != "customer":
        flash("Only customers can submit feedback.", "danger")
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        rating = request.form["rating"]
        feedback_text = request.form["feedback"]  # changed from comment
        cursor.execute(
            "INSERT INTO Feedback (comment, rating, product_id, user_id, submitted_at) VALUES (%s, %s, %s, %s, NOW())",
            (feedback_text, rating, product_id, user["id"])
        )
        conn.commit()
        flash("Feedback submitted successfully!", "success")
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    # Get product info + vendor name
    cursor.execute("""
        SELECT p.id, p.name, p.description, v.name AS vendor_name
        FROM Products p
        JOIN Vendors v ON p.vendor_id = v.id
        WHERE p.id = %s
    """, (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("feedback_form.html", product=product, user=user)



@app.route("/reply/<int:feedback_id>", methods=["GET", "POST"])
def reply(feedback_id):
    user = current_user()
    if not user or user["role"] != "admin":
        flash("Only admins can reply.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        reply_text = request.form["reply_text"]

        # In real setup, map admin to vendor_id properly
        vendor_id = 1  

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Review_Replies (reply_text, feedback_id, vendor_id) VALUES (%s, %s, %s)",
            (reply_text, feedback_id, vendor_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Reply posted!", "success")
        return redirect(url_for("home"))

    return render_template("reply_form.html", feedback_id=feedback_id, user=user)


if __name__ == "__main__":
    app.run(debug=True)
