import os
os.system("mysql -u flaskuser -prishisuren < init.sql")
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"

# --- Configure DB connection (change credentials as needed) ---
DB_CONFIG = {
    "host": "localhost",
    "user": "flaskuser",
    "password": "rishisuren",   # <-- change
    "database": "feedback_system"
}

def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"DB connection error: {e}")

# --- Helper: fetch lists for forms ---
def fetch_lookup_data():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name FROM users ORDER BY name")
    users = cur.fetchall()
    cur.execute("SELECT id, name FROM vendors ORDER BY name")
    vendors = cur.fetchall()
    cur.execute("SELECT id, name FROM products ORDER BY name")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return users, vendors, products

# --- Home / Read all ---
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Feedbacks with optional reply/vender
    cur.execute("""
        SELECT f.id AS feedback_id, f.comment, f.rating, f.submitted_at,
               f.product_id, f.user_id,
               u.name AS user_name, p.name AS product_name,
               rr.id AS reply_id, rr.reply_text, rr.vendor_id AS reply_vendor_id, v.name AS reply_vendor_name
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        JOIN products p ON f.product_id = p.id
        LEFT JOIN review_replies rr ON rr.feedback_id = f.id
        LEFT JOIN vendors v ON rr.vendor_id = v.id
        ORDER BY f.submitted_at DESC
    """)
    feedbacks = cur.fetchall()

    # Products
    cur.execute("""
        SELECT p.id, p.name, p.description, p.vendor_id, p.created_at, v.name AS vendor_name
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.id
        ORDER BY p.created_at DESC
    """)
    products = cur.fetchall()

    # Users
    cur.execute("SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC")
    users = cur.fetchall()

    # Vendors
    cur.execute("SELECT id, name, contact_email FROM vendors ORDER BY name")
    vendors = cur.fetchall()

    cur.close()
    conn.close()

    lookup_users, lookup_vendors, lookup_products = users, vendors, products
    return render_template("index.html",
                           feedbacks=feedbacks,
                           products=products,
                           users=users,
                           vendors=vendors,
                           lookup_users=lookup_users,
                           lookup_vendors=lookup_vendors,
                           lookup_products=lookup_products)

# -------------------- USERS --------------------
@app.route("/users/create", methods=["POST"])
def create_user():
    name = request.form.get("name")
    email = request.form.get("email")
    role = request.form.get("role") or None
    if not name or not email:
        flash("Name and email required for user.", "danger")
        return redirect(url_for("index"))
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, role, created_at) VALUES (%s,%s,%s,NOW())",
                    (name, email, role))
        conn.commit()
        flash("User created.", "success")
    except Error as e:
        flash(f"Error creating user: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/users/update/<int:user_id>", methods=["POST"])
def update_user(user_id):
    name = request.form.get("name")
    email = request.form.get("email")
    role = request.form.get("role") or None
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET name=%s, email=%s, role=%s WHERE id=%s",
                    (name, email, role, user_id))
        conn.commit()
        flash("User updated.", "success")
    except Error as e:
        flash(f"Error updating user: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        flash("User deleted.", "success")
    except Error as e:
        flash(f"Error deleting user: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

# -------------------- VENDORS --------------------
@app.route("/vendors/create", methods=["POST"])
def create_vendor():
    name = request.form.get("name")
    contact = request.form.get("contact_email")
    if not name or not contact:
        flash("Vendor name and contact required.", "danger")
        return redirect(url_for("index"))
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO vendors (name, contact_email) VALUES (%s,%s)", (name, contact))
        conn.commit()
        flash("Vendor created.", "success")
    except Error as e:
        flash(f"Error creating vendor: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/vendors/update/<int:vendor_id>", methods=["POST"])
def update_vendor(vendor_id):
    name = request.form.get("name")
    contact = request.form.get("contact_email")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE vendors SET name=%s, contact_email=%s WHERE id=%s",
                    (name, contact, vendor_id))
        conn.commit()
        flash("Vendor updated.", "success")
    except Error as e:
        flash(f"Error updating vendor: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/vendors/delete/<int:vendor_id>", methods=["POST"])
def delete_vendor(vendor_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM vendors WHERE id=%s", (vendor_id,))
        conn.commit()
        flash("Vendor deleted.", "success")
    except Error as e:
        flash(f"Error deleting vendor: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

# -------------------- PRODUCTS --------------------
@app.route("/products/create", methods=["POST"])
def create_product():
    name = request.form.get("name")
    description = request.form.get("description") or None
    vendor_id = request.form.get("vendor_id") or None
    if not name:
        flash("Product name required.", "danger")
        return redirect(url_for("index"))
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO products (name, description, vendor_id, created_at) VALUES (%s,%s,%s,NOW())",
                    (name, description, vendor_id))
        conn.commit()
        flash("Product created.", "success")
    except Error as e:
        flash(f"Error creating product: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/products/update/<int:product_id>", methods=["POST"])
def update_product(product_id):
    name = request.form.get("name")
    description = request.form.get("description") or None
    vendor_id = request.form.get("vendor_id") or None
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE products SET name=%s, description=%s, vendor_id=%s WHERE id=%s",
                    (name, description, vendor_id, product_id))
        conn.commit()
        flash("Product updated.", "success")
    except Error as e:
        flash(f"Error updating product: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
        conn.commit()
        flash("Product deleted.", "success")
    except Error as e:
        flash(f"Error deleting product: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

# -------------------- FEEDBACK --------------------
@app.route("/feedback/create", methods=["POST"])
def create_feedback():
    user_id = request.form.get("user_id")
    product_id = request.form.get("product_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment") or None

    # Basic validation
    if not user_id or not product_id or not rating:
        flash("User, product and rating are required.", "danger")
        return redirect(url_for("index"))
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError()
    except:
        flash("Rating must be integer 1-5.", "danger")
        return redirect(url_for("index"))

    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO feedback (comment, rating, submitted_at, product_id, user_id)
                       VALUES (%s,%s,NOW(),%s,%s)""",
                    (comment, rating_int, product_id, user_id))
        conn.commit()
        flash("Feedback created.", "success")
    except Error as e:
        flash(f"Error creating feedback: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/feedback/update/<int:feedback_id>", methods=["POST"])
def update_feedback(feedback_id):
    comment = request.form.get("comment") or None
    rating = request.form.get("rating")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE feedback SET comment=%s, rating=%s WHERE id=%s", (comment, rating, feedback_id))
        conn.commit()
        flash("Feedback updated.", "success")
    except Error as e:
        flash(f"Error updating feedback: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/feedback/delete/<int:feedback_id>", methods=["POST"])
def delete_feedback(feedback_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM feedback WHERE id=%s", (feedback_id,))
        conn.commit()
        flash("Feedback deleted.", "success")
    except Error as e:
        flash(f"Error deleting feedback: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

# -------------------- REVIEW REPLIES --------------------
@app.route("/replies/create", methods=["POST"])
def create_reply():
    feedback_id = request.form.get("feedback_id")
    vendor_id = request.form.get("vendor_id")
    reply_text = request.form.get("reply_text") or None
    if not feedback_id or not vendor_id:
        flash("Feedback and vendor required for a reply.", "danger")
        return redirect(url_for("index"))
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO review_replies (feedback_id, vendor_id, reply_text, replied_at) VALUES (%s,%s,%s,NOW())",
                    (feedback_id, vendor_id, reply_text))
        conn.commit()
        flash("Reply created.", "success")
    except Error as e:
        flash(f"Error creating reply: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/replies/update/<int:reply_id>", methods=["POST"])
def update_reply(reply_id):
    reply_text = request.form.get("reply_text") or None
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE review_replies SET reply_text=%s WHERE id=%s", (reply_text, reply_id))
        conn.commit()
        flash("Reply updated.", "success")
    except Error as e:
        flash(f"Error updating reply: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

@app.route("/replies/delete/<int:reply_id>", methods=["POST"])
def delete_reply(reply_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM review_replies WHERE id=%s", (reply_id,))
        conn.commit()
        flash("Reply deleted.", "success")
    except Error as e:
        flash(f"Error deleting reply: {e}", "danger")
    finally:
        cur.close(); conn.close()
    return redirect(url_for("index"))

# -------------------- Run app --------------------
if __name__ == "__main__":
    app.run(debug=True)
