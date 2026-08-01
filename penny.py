import requests
import sqlite3

BASE_URL = "https://www.penny.ro"

API_URL = (
    "https://www.penny.ro/api/product-discovery/categories/"
    "oferte-site-kw31-oferte-penny-card/products"
)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.penny.ro/oferte-card"
}


# SQLite setup
conn = sqlite3.connect("penny_products.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    url TEXT,
    image TEXT,
    regular_price TEXT,
    card_price TEXT,
    regular_unit_price TEXT,
    card_unit_price TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Add image if database already existed
cursor.execute("PRAGMA table_info(products)")
columns = [column[1] for column in cursor.fetchall()]

if "image" not in columns:
    cursor.execute("""
        ALTER TABLE products
        ADD COLUMN image TEXT
    """)

conn.commit()


# Save/update product
def save_product(product):
    cursor.execute("""
        INSERT INTO products (
            id,
            name,
            url,
            image,
            regular_price,
            card_price,
            regular_unit_price,
            card_unit_price,
            updated_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

        ON CONFLICT(id)
        DO UPDATE SET
            name = excluded.name,
            url = excluded.url,
            image = excluded.image,
            regular_price = excluded.regular_price,
            card_price = excluded.card_price,
            regular_unit_price = excluded.regular_unit_price,
            card_unit_price = excluded.card_unit_price,
            updated_at = CURRENT_TIMESTAMP
    """, (
        product["id"],
        product["name"],
        product["url"],
        product["image"],
        product["regular_price"],
        product["card_price"],
        product["regular_unit_price"],
        product["card_unit_price"]
    ))

    conn.commit()


# Helpers
def format_price(value):
    if value is None:
        return None

    return f"{value / 100:.2f}"


# Scrape API pages
all_products = []

page = 0
page_size = 50


while True:

    params = {
        "page": page,
        "pageSize": page_size
    }

    response = requests.get(
        API_URL,
        headers=headers,
        params=params
    )


    if response.status_code != 200:
        print(
            "Request failed:",
            response.status_code
        )
        break


    data = response.json()

    results = data.get("results", [])

    print(f"Page {page}: {len(results)} products")


    if not results:
        break



    for index, item in enumerate(results):

        # Generate scraper ID
        product_id = (page * page_size) + index + 1


        price = item.get("price", {})

        regular = price.get("regular", {})

        loyalty = price.get("loyalty", {})


        # Image URL
        image = None

        if item.get("images"):
            image = item["images"][0]


        product = {
            "id": product_id,

            "name": item.get("name"),

            "url": (
                BASE_URL +
                "/products/" +
                item.get("slug", "")
            ),

            "image": image,

            "regular_price": format_price(
                regular.get("value")
            ),

            "card_price": format_price(
                loyalty.get("value")
            ),

            "regular_unit_price": format_price(
                regular.get("perStandardizedQuantity")
            ),

            "card_unit_price": format_price(
                loyalty.get("perStandardizedQuantity")
            )
        }


        save_product(product)

        all_products.append(product)



    page += 1


    # Last page
    if len(results) < page_size:
        break



conn.close()


print("\nTOTAL:", len(all_products))
