import json
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.lidl.ro"

headers = { "User-Agent": "Mozilla/5.0" }

def get_weekly_offers_url():
    html = requests.get(BASE_URL, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    tiles = soup.select("a.ABaseContentTile__content")

    for tile in tiles:
        title = tile.select_one(".ABaseContentTile__title")
        if title and "Lidl Plus" in title.get_text(strip=True):
            return urljoin(BASE_URL, tile["href"])

    raise Exception("Could not find Lidl Plus weekly offers URL")

# Automatically find current weekly offers URL
URL = get_weekly_offers_url()
print(f"Using URL: {URL}")

# SQLite setup
conn = sqlite3.connect("lidl_products.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT UNIQUE,
    title TEXT,
    price REAL,
    old_price REAL,
    currency TEXT,
    image TEXT,
    url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# Download Lidl page
html = requests.get(URL, headers=headers).text
soup = BeautifulSoup(html, "html.parser")
products = soup.select('[data-selector="PRODUCT"]')
print(f"Found {len(products)} products")

# Parse products
for product in products:
    try:
        data = json.loads(product["data-grid-data"])
        title = data.get("title")
        product_id = str(data.get("productId"))
        image = data.get("image")
        price = None
        old_price = None
        currency = "Lei"

        # Price extraction
        region = data.get("regionsPrices", {}).get("1", {})

        if "currentLidlPlusPrice" in region:
            info = region["currentLidlPlusPrice"]["price"]
            price = info.get("price")
            old_price = info.get("oldPrice")
            currency = info.get("currencySymbol", "Lei")

        elif "currentPrice" in region:
            info = region["currentPrice"]["price"]
            if isinstance(info, dict):
                price = info.get("price")
                old_price = info.get("oldPrice")
                currency = info.get("currencySymbol", "Lei")

        elif data.get("lidlPlus"):
            info = data["lidlPlus"][0]["price"]
            if isinstance(info, dict):
                price = info.get("price")

        elif "price" in data:
            info = data["price"]
            if isinstance(info, dict):
                price = info.get("price")
                currency = info.get("currencySymbol", "Lei")
            else:
                price = info

        product_url = ("https://www.lidl.ro" + data.get("canonicalUrl", ""))

        cursor.execute("""
        INSERT INTO products
        (
            product_id,
            title,
            price,
            old_price,
            currency,
            image,
            url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(product_id)
        DO UPDATE SET
            title=excluded.title,
            price=excluded.price,
            old_price=excluded.old_price,
            currency=excluded.currency,
            image=excluded.image,
            url=excluded.url
        """,
        (
            product_id,
            title,
            price,
            old_price,
            currency,
            image,
            product_url
        ))

        conn.commit()
        print(f"Saved: {title}")

    except Exception as e:
        print("\nERROR:")
        print(e)

        try:
            print("Product:", data.get("title"))
        except:
            pass

        continue

conn.close()
print("\nDone")
