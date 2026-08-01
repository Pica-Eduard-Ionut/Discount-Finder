from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

LIDL_DB = "lidl_products.db"
PENNY_DB = "penny_products.db"

def get_lidl_products(search=""):
    conn = sqlite3.connect(LIDL_DB)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT
            title AS name,
            old_price,
            price AS new_price,
            image,
            url,
            'Lidl' AS supermarket
        FROM products
    """
    params = []
    if search:
        query += " WHERE title LIKE ?"
        params.append(f"%{search}%")

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_penny_products(search=""):
    conn = sqlite3.connect(PENNY_DB)
    conn.row_factory = sqlite3.Row
    query = """
        SELECT
            name,
            regular_price AS old_price,
            card_price AS new_price,
            image,
            url,
            'Penny' AS supermarket
        FROM products
    """
    params = []
    if search:
        query += " WHERE name LIKE ?"
        params.append(f"%{search}%")

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return rows

def calculate_discount(old_price, new_price):
    try:
        old_price = float(old_price)
        new_price = float(new_price)

        if old_price > new_price:
            return round(((old_price - new_price) / old_price) * 100)
    except:
        pass

    return None

@app.route("/")
def index():
    search = request.args.get("q", "")
    products = []
    products.extend(get_lidl_products(search))
    products.extend(get_penny_products(search))
    # calculate discounts
    processed_products = []

    for p in products:
        product = dict(p)
        product["discount"] = calculate_discount(
            product.get("old_price"),
            product.get("new_price")
        )
        processed_products.append(product)

    # total products in databases
    conn = sqlite3.connect(LIDL_DB)
    lidl_count = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]
    conn.close()

    conn = sqlite3.connect(PENNY_DB)
    penny_count = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]
    conn.close()

    total_products = lidl_count + penny_count

    return render_template(
        "index.html",
        products=processed_products,
        search=search,
        total_products=total_products
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
