import os
import requests
from bs4 import BeautifulSoup
from pinterest.client import Pinterest
import schedule
import time
import json
import random

# -------- CONFIG FROM ENV --------
REDBUBBLE_STORE_URL = os.getenv("REDBUBBLE_STORE_URL")  # e.g. https://www.redbubble.com/people/your-shop/shop
PINTEREST_ACCESS_TOKEN = os.getenv("PINTEREST_ACCESS_TOKEN")
PINTEREST_BOARD_ID = os.getenv("PINTEREST_BOARD_ID")
STATE_FILE = "posted_products.json"
POST_TIMES = ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"]  # every 4 hours
# ---------------------------------

def scrape_redbubble_products(store_url):
    """Scrape product titles, images, and links from your Redbubble store"""
    products = []
    response = requests.get(store_url)
    if response.status_code != 200:
        print("Error fetching store page")
        return products
    
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all("a", class_="styles__link--1wv3r")  # class may change
    
    for item in items:
        link = "https://www.redbubble.com" + item.get("href")
        title = item.get("title", "Redbubble Product")
        img_tag = item.find("img")
        img_url = img_tag.get("src") if img_tag else None
        
        products.append({
            "title": title,
            "link": link,
            "image": img_url
        })
    return products

def load_posted():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open(STATE_FILE, "w") as f:
        json.dump(list(posted), f)

def post_to_pinterest(product, pinterest_client):
    """Post one product to Pinterest"""
    try:
        pinterest_client.pins.create(
            board_id=PINTEREST_BOARD_ID,
            title=product["title"],
            description=f"Check out my Redbubble product: {product['title']}",
            link=product["link"],
            media_source={"source_type": "image_url", "url": product["image"]}
        )
        print(f"✅ Posted: {product['title']}")
        return True
    except Exception as e:
        print(f"❌ Error posting {product['title']}: {e}")
        return False

def job():
    # Load products
    products = scrape_redbubble_products(REDBUBBLE_STORE_URL)
    posted = load_posted()
    
    # Filter out already posted
    new_products = [p for p in products if p["link"] not in posted]
    if not new_products:
        print("No new products to post.")
        return
    
    # Pick one product at random
    product = random.choice(new_products)
    
    # Connect to Pinterest
    pinterest = Pinterest(access_token=PINTEREST_ACCESS_TOKEN)
    
    # Post
    if post_to_pinterest(product, pinterest):
        posted.add(product["link"])
        save_posted(posted)

def main():
    # Schedule jobs every 4 hours
    for t in POST_TIMES:
        schedule.every().day.at(t).do(job)
        print(f"📅 Scheduled post at {t}")
    
    # Loop forever (only needed if you run locally, not on GitHub Actions)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
