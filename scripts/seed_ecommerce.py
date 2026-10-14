"""Fill a DEV Firestore with demo marketplace data for ecommerce-mcp-server.

Creates categories, sellers, products (real brand names, demo prices), product reviews,
seller reviews, 300 customers, orders, returns, and YOUR account with orders in every status.
Prices, sellers and reviews are fictional demo data.

Run from the project root:
    python -m scripts.seed_store            # add data
    python -m scripts.seed_store --reset    # delete old demo data first, then add
"""

import argparse
import os
import random
from datetime import datetime, timedelta, timezone

import firebase_admin
from dotenv import load_dotenv
from faker import Faker
from firebase_admin import auth, credentials, firestore

load_dotenv()
random.seed(7)
Faker.seed(7)
fake = Faker()
NOW = datetime.now(timezone.utc)

USER_COUNT = 300
SELLER_COUNT = 40
ORDER_COUNT = 600
SHIPPING_FEE = int(os.getenv("SHIPPING_FEE_PKR", 150))
FREE_SHIPPING_ABOVE = int(os.getenv("FREE_SHIPPING_ABOVE_PKR", 2000))

COLLECTIONS = ["categories", "sellers", "products", "reviews", "seller_reviews", "users", "orders", "returns"]

# ---------- catalog: (brand, model, (min_price, max_price), variants) ----------
CATALOG = {
    "mobiles": {"name": "Mobiles", "items": [
        ("Samsung", "Galaxy A15", (38000, 45000), ["Black", "Light Blue", "Yellow"]),
        ("Samsung", "Galaxy A55", (110000, 125000), ["Navy", "Lilac", "Ice Blue"]),
        ("Samsung", "Galaxy S24", (260000, 290000), ["Onyx Black", "Marble Grey"]),
        ("Xiaomi", "Redmi 13C", (28000, 33000), ["Midnight Black", "Navy Blue", "Clover Green"]),
        ("Xiaomi", "Redmi Note 13", (50000, 60000), ["Graphite Black", "Ocean Sunset"]),
        ("Xiaomi", "Redmi Note 13 Pro", (78000, 90000), ["Midnight Black", "Aurora Purple"]),
        ("Infinix", "Hot 40 Pro", (36000, 42000), ["Starlit Black", "Palm Blue"]),
        ("Infinix", "Note 40", (52000, 60000), ["Obsidian Black", "Titan Gold"]),
        ("Tecno", "Spark 20 Pro", (38000, 45000), ["Moonlit Black", "Frosty Ivory"]),
        ("Apple", "iPhone 15", (300000, 340000), ["Black", "Blue", "Pink"]),
        ("Vivo", "Y28", (42000, 48000), ["Crystal Purple", "Agate Black"]),
        ("Oppo", "Reno 11F", (80000, 90000), ["Palm Green", "Ocean Blue"]),
    ]},
    "electronics": {"name": "Electronics", "items": [
        ("Apple", "AirPods Pro (2nd Gen)", (65000, 75000), ["White"]),
        ("Samsung", "Galaxy Buds FE", (18000, 24000), ["Graphite", "White"]),
        ("Anker", "Soundcore Life P3", (12000, 16000), ["Black", "Navy"]),
        ("JBL", "Flip 6 Speaker", (28000, 35000), ["Black", "Blue", "Red"]),
        ("JBL", "Tune 520BT Headphones", (11000, 14000), ["Black", "White", "Blue"]),
        ("Audionic", "Airbud 590", (4000, 6000), ["Black", "White"]),
        ("Xiaomi", "Smart Band 8", (8000, 10500), ["Black", "Gold"]),
        ("Xiaomi", "Power Bank 20000mAh", (5000, 7500), ["Black", "White"]),
        ("Anker", "20W USB-C Charger", (2500, 3800), ["White"]),
        ("Logitech", "M331 Silent Mouse", (3500, 4800), ["Black", "Red", "Blue"]),
        ("Lenovo", "IdeaPad Slim 3 Laptop", (150000, 185000), ["Arctic Grey"]),
        ("HP", "Victus 15 Gaming Laptop", (210000, 250000), ["Mica Silver", "Performance Blue"]),
    ]},
    "fashion": {"name": "Fashion", "items": [
        ("Khaadi", "Lawn 3-Piece Unstitched", (5500, 8500), ["Pink", "Mint", "Mustard"]),
        ("Gul Ahmed", "Embroidered Lawn Suit", (6000, 9500), ["Peach", "Sky Blue", "Maroon"]),
        ("Sapphire", "Printed Kurta", (3500, 5500), ["Black", "Teal", "Off White"]),
        ("J.", "Men's Kurta Shalwar", (5000, 8000), ["White", "Navy", "Grey"]),
        ("Outfitters", "Graphic T-Shirt", (1500, 2500), ["Black", "White", "Olive"]),
        ("Outfitters", "Slim Fit Denim Jeans", (3500, 5000), ["Dark Blue", "Light Blue", "Black"]),
        ("Nike", "Air Max SC Sneakers", (22000, 28000), ["White", "Black"]),
        ("Adidas", "Duramo Running Shoes", (15000, 19000), ["Core Black", "Cloud White"]),
        ("Bata", "Leather Formal Shoes", (6500, 9000), ["Black", "Brown"]),
        ("Servis", "Casual Slippers", (1200, 2200), ["Black", "Brown", "Navy"]),
    ]},
    "bags": {"name": "Bags & Luggage", "items": [
        ("Samsonite", "Cabin Trolley 55cm", (45000, 60000), ["Black", "Navy", "Red"]),
        ("American Tourister", "Laptop Backpack", (9000, 13000), ["Black", "Grey"]),
        ("Hush Puppies", "Leather Wallet", (4000, 6500), ["Brown", "Black"]),
        ("Charles & Keith", "Shoulder Bag", (14000, 19000), ["Black", "Taupe", "Cream"]),
        ("Sapphire", "Canvas Tote Bag", (2500, 4000), ["Beige", "Black"]),
        ("Nike", "Gym Duffel Bag", (9000, 12000), ["Black", "Grey"]),
        ("Generic", "Women's Crossbody Bag", (1800, 3500), ["Black", "Pink", "Brown", "White"]),
        ("Generic", "School Backpack", (1500, 3000), ["Blue", "Black", "Red"]),
        ("Stylo", "Party Clutch", (3000, 5000), ["Gold", "Silver", "Black"]),
        ("Generic", "Travel Organizer Pouch", (800, 1500), ["Grey", "Navy"]),
    ]},
    "home_kitchen": {"name": "Home & Kitchen", "items": [
        ("Philips", "Air Fryer HD9200", (28000, 35000), ["Black"]),
        ("Philips", "Hand Blender HR2530", (9000, 12000), ["White"]),
        ("Philips", "Steam Iron GC1905", (6500, 8500), ["Blue"]),
        ("Anex", "Juicer Blender AG-176", (7000, 9500), ["White"]),
        ("Westpoint", "Electric Kettle WF-6175", (4500, 6000), ["Silver"]),
        ("Dawlance", "Microwave Oven DW-115", (28000, 34000), ["Black"]),
        ("Kenwood", "Stand Mixer KHC29", (45000, 55000), ["White"]),
        ("Sonex", "Non-Stick Cookware Set", (9000, 14000), ["Red", "Black"]),
        ("Generic", "Cotton Bedsheet Set", (2500, 4500), ["White", "Grey", "Floral"]),
        ("Generic", "LED Desk Lamp", (1500, 3000), ["White", "Black"]),
    ]},
    "beauty": {"name": "Health & Beauty", "items": [
        ("L'Oreal Paris", "Revitalift Hyaluronic Serum", (3500, 4800), ["30ml"]),
        ("Maybelline", "Fit Me Foundation", (2200, 3200), ["120 Classic Ivory", "220 Natural Beige", "310 Sun Beige"]),
        ("Garnier", "Micellar Cleansing Water", (1200, 1800), ["400ml"]),
        ("Nivea", "Nourishing Body Lotion", (900, 1400), ["400ml"]),
        ("Pond's", "Bright Beauty Face Wash", (600, 900), ["100g"]),
        ("Conatural", "Rose Water Toner", (700, 1100), ["120ml"]),
        ("J.", "Janan Perfume", (4500, 6500), ["100ml"]),
        ("Dove", "Intense Repair Shampoo", (1100, 1600), ["360ml"]),
        ("Neutrogena", "Hydro Boost Water Gel", (4000, 5500), ["50ml"]),
        ("Generic", "Makeup Brush Set", (1200, 2500), ["Pink", "Black"]),
    ]},
    "sports": {"name": "Sports & Outdoors", "items": [
        ("CA Sports", "Plus 15000 Cricket Bat", (14000, 22000), ["Short Handle"]),
        ("CA Sports", "Tape Ball Cricket Bat", (2500, 4000), ["Light", "Heavy"]),
        ("Adidas", "Football Size 5", (4500, 7000), ["White/Black", "White/Blue"]),
        ("Yonex", "Muscle Power Badminton Racket", (5500, 8000), ["Black/Red", "Blue"]),
        ("Nike", "Training Gloves", (3500, 5000), ["Black"]),
        ("Generic", "Yoga Mat 6mm", (1800, 3000), ["Purple", "Blue", "Black"]),
        ("Generic", "Dumbbell Pair 5kg", (4000, 6500), ["Black"]),
        ("Generic", "Resistance Bands Set", (1200, 2200), ["Multicolor"]),
        ("Generic", "Skipping Rope", (500, 1000), ["Black", "Blue"]),
        ("Generic", "Cycling Helmet", (3000, 5500), ["Black", "White"]),
    ]},
    "watches": {"name": "Watches & Accessories", "items": [
        ("Casio", "G-Shock GA-2100", (28000, 36000), ["Black", "Olive"]),
        ("Casio", "Vintage A168", (9000, 12000), ["Silver", "Gold"]),
        ("Fossil", "Grant Chronograph", (45000, 60000), ["Brown Leather", "Black"]),
        ("Xiaomi", "Redmi Watch 3 Active", (9000, 12000), ["Black", "Grey"]),
        ("Samsung", "Galaxy Watch 6 40mm", (55000, 70000), ["Graphite", "Gold"]),
        ("Ray-Ban", "Aviator Classic Sunglasses", (25000, 35000), ["Gold/Green", "Black"]),
        ("Generic", "Polarized Sunglasses", (1200, 2500), ["Black", "Brown"]),
        ("Generic", "Smart Watch T500", (2500, 4000), ["Black", "Pink", "Blue"]),
        ("Curren", "Analog Men's Watch", (4500, 7000), ["Black", "Blue"]),
        ("Generic", "Leather Watch Strap", (800, 1500), ["Brown", "Black"]),
    ]},
}

# ---------- review text (mild, everyday comments) ----------
CATEGORY_PHRASES = {
    "mobiles": {"good": ["Camera is excellent in daylight.", "Battery easily lasts a full day.", "PTA approved with original box.",
                         "Display is bright and smooth.", "Phone bohat smooth chal raha hai."],
                "bad": ["Phone gets warm while gaming.", "Battery drains faster than expected.", "Box looked opened before delivery.",
                        "Camera is average in low light.", "Charger box mein nahi tha."]},
    "electronics": {"good": ["Sound is clear with good bass.", "Connects quickly with my phone.", "Build quality feels premium.",
                             "Battery backup is great.", "Awaz bohat zabardast hai."],
                    "bad": ["Stopped working after two weeks.", "Bluetooth keeps disconnecting.", "Sound is weaker than advertised.",
                            "Charging is very slow.", "Quality expectation se kam thi."]},
    "fashion": {"good": ["Fabric is soft and comfortable.", "Colour is exactly like the picture.", "Stitching is neat.",
                         "Size fits perfectly.", "Kapra bohat acha hai."],
                "bad": ["Colour faded after the first wash.", "Size runs small, order one size up.", "Fabric is thinner than expected.",
                        "Stitching came loose.", "Picture se thora different hai."]},
    "bags": {"good": ["Leather quality is great.", "Lots of space and pockets.", "Zips are smooth and strong.",
                      "Looks even better in real life.", "Bag bohat stylish hai."],
             "bad": ["Strap broke within a month.", "Strong smell when opened.", "Smaller than it looks in pictures.",
                     "Zip got stuck on day two.", "Colour picture se mukhtalif tha."]},
    "home_kitchen": {"good": ["Works perfectly and saves time.", "Easy to clean.", "Powerful motor.",
                              "Good value for the price.", "Ammi ko bohat pasand aaya."],
                     "bad": ["Too noisy.", "Stopped working after a few uses.", "Plastic feels cheap.",
                             "Received with a broken part.", "Warranty card missing tha."]},
    "beauty": {"good": ["Suits my skin, no irritation.", "Lasts all day.", "Smells lovely.",
                        "Visible results in two weeks.", "Original product hai."],
               "bad": ["Did not suit my skin.", "Expiry date was close.", "Felt watered down.",
                       "Fragrance fades in an hour.", "Packing leak thi."]},
    "sports": {"good": ["Great grip and balance.", "Sturdy and well made.", "Perfect for daily practice.",
                        "Light weight and durable.", "Bat ka stroke bohat acha hai."],
               "bad": ["Handle came loose.", "Wore out quickly.", "Smaller than described.",
                       "Grip is slippery.", "Delivery mein thora damage tha."]},
    "watches": {"good": ["Looks premium on the wrist.", "Keeps accurate time.", "Strap is comfortable.",
                         "Great features for the price.", "Bohat classy watch hai."],
                "bad": ["Glass scratches easily.", "Strap broke after a month.", "Battery died quickly.",
                        "Looks cheaper than the pictures.", "Time thora aage peeche hota hai."]},
}
GENERIC_GOOD = ["Fast delivery and good packing.", "Highly recommended.", "Exactly as described.",
                "Value for money.", "Delivery time par hui, shukriya."]
GENERIC_MID = ["Okay for the price.", "Average quality, nothing special.",
               "Delivery was late but the product is fine.", "Theek hai, itna khaas nahi."]
GENERIC_BAD = ["Not worth the money.", "Very disappointed.", "Seller did not reply to my messages.",
               "Would not buy again.", "Paise zaya ho gaye."]
TITLES = {5: ["Excellent!", "Loved it", "Totally worth it"], 4: ["Very good", "Happy with it", "Good buy"],
          3: ["It's okay", "Average", "Mixed feelings"], 2: ["Not great", "Disappointed", "Below expectations"],
          1: ["Terrible", "Do not buy", "Waste of money"]}
SELLER_GOOD = ["Fast delivery and safe packing.", "Seller replied quickly.", "Item was exactly as listed.",
               "Second order from this seller, always good.", "Seller bohat cooperative hai."]
SELLER_MID = ["Delivery was okay.", "Average experience.", "Packing could be better."]
SELLER_BAD = ["Delivery was very late.", "Poor packing, item arrived damaged.", "Seller ignored my messages.",
              "Sent the wrong colour.", "Refund mein bohat time laga."]

# ---------- people and places ----------
FIRST_NAMES = ["Ali", "Ahmed", "Hamza", "Usman", "Bilal", "Hassan", "Zain", "Fahad", "Saad", "Umar", "Talha",
               "Danish", "Waseem", "Rehan", "Mustafa", "Kashif", "Adeel", "Hamid", "Shahzaib", "Imran",
               "Ayesha", "Fatima", "Hira", "Zara", "Sana", "Mahnoor", "Iqra", "Noor", "Areeba", "Laiba", "Mehak", "Maryam"]
LAST_NAMES = ["Khan", "Ahmed", "Malik", "Butt", "Sheikh", "Raza", "Qureshi", "Chaudhry", "Hussain", "Iqbal",
              "Asghar", "Javed", "Siddiqui", "Mirza", "Abbasi", "Shah", "Baig", "Rana", "Akhtar", "Nawaz"]
CITIES = ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar", "Sialkot", "Hyderabad", "Quetta"]
AREAS = ["Model Town", "Gulberg", "DHA Phase 5", "Johar Town", "Bahria Town", "Satellite Town", "Cantt",
         "Gulshan-e-Iqbal", "Clifton", "F-10", "G-11", "University Town", "Garden Town", "Saddar"]
SELLER_A = ["Tech", "Smart", "Style", "Urban", "Prime", "Mega", "Galaxy", "Royal", "Classic", "Daily", "Trendy", "Value"]
SELLER_B = ["Zone", "Mart", "Hub", "Store", "Point", "House", "Corner", "Outlet", "World", "Express"]
PAYMENTS = ["COD"] * 55 + ["Card"] * 15 + ["JazzCash"] * 15 + ["EasyPaisa"] * 15
COURIERS = ["TCS", "Leopards", "M&P", "Trax"]
RETURN_REASONS = ["Wrong colour received", "Item damaged on arrival", "Size does not fit",
                  "Not as described", "Received a different product", "Quality is poor"]

# order status -> how many days ago it was placed
ORDER_STATUSES = (["delivered"] * 55 + ["shipped"] * 8 + ["confirmed"] * 5 + ["placed"] * 5
                  + ["cancelled"] * 12 + ["returned"] * 8 + ["return_requested"] * 4)
AGE_DAYS = {"placed": (0.05, 0.9), "confirmed": (1, 3), "shipped": (3, 6), "delivered": (5, 150),
            "cancelled": (1, 150), "returned": (15, 150), "return_requested": (8, 14)}
FLOW = ["placed", "confirmed", "shipped", "delivered"]

# your own orders: (status, placed this many days ago)
MY_ORDERS = [("placed", 0.1), ("confirmed", 1.5), ("shipped", 4), ("delivered", 4),
             ("delivered", 25), ("cancelled", 10), ("returned", 40)]


# ---------- small helpers ----------
def clamp(value, low, high):
    return max(low, min(high, value))


def demo_price(value: float) -> int:
    """34,512 -> 34,499 (shop-style price)."""
    step = 100 if value >= 1000 else 10
    return max(step - 1, int(round(value / step) * step) - 1)


def pick_stars(quality: float) -> int:
    """Higher hidden quality -> more stars, but always some good and bad reviews."""
    return int(clamp(round(random.gauss(1 + 4 * quality, 0.9)), 1, 5))


def short_name(full_name: str) -> str:
    first, last = full_name.split(" ", 1)
    return f"{first} {last[0]}."


def review_comment(category: str, stars: int) -> str:
    phrases = CATEGORY_PHRASES[category]
    if stars >= 4:
        parts = [random.choice(phrases["good"])] + random.sample(GENERIC_GOOD, k=random.randint(0, 1))
    elif stars == 3:
        parts = [random.choice(phrases["good"]), random.choice(phrases["bad"])] if random.random() < 0.5 else [random.choice(GENERIC_MID)]
    else:
        parts = [random.choice(phrases["bad"])] + random.sample(GENERIC_BAD, k=random.randint(0, 1))
    return " ".join(parts)


def seller_comment(stars: int) -> str:
    return random.choice(SELLER_GOOD if stars >= 4 else SELLER_MID if stars == 3 else SELLER_BAD)


def random_address(city: str) -> dict:
    return {"line": f"House {random.randint(1, 999)}, Street {random.randint(1, 40)}, {random.choice(AREAS)}", "city": city}


# ---------- Firebase ----------
def start_firebase():
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "firebase-key.json"))
    firebase_admin.initialize_app(cred)
    return firestore.client()


def write_all(db, collection: str, docs: dict[str, dict]) -> None:
    """Write documents in batches. Keys starting with '_' are hidden helpers and are not saved."""
    batch, count = db.batch(), 0
    for doc_id, data in docs.items():
        clean = {k: v for k, v in data.items() if not k.startswith("_")}
        batch.set(db.collection(collection).document(doc_id), {**clean, "seeded": True})
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"  {collection}: {len(docs)}")


def delete_seeded(db) -> None:
    for collection in COLLECTIONS:
        docs = list(db.collection(collection).where("seeded", "==", True).stream())
        batch = db.batch()
        for i, doc in enumerate(docs, start=1):
            batch.delete(doc.reference)
            if i % 400 == 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        print(f"  {collection}: {len(docs)} deleted")


# ---------- data builders ----------
def make_categories() -> dict[str, dict]:
    return {cid: {"name": c["name"]} for cid, c in CATALOG.items()}


def make_sellers() -> dict[str, dict]:
    sellers, used, categories = {}, set(), list(CATALOG)
    for i in range(SELLER_COUNT):
        city = random.choice(CITIES)
        name = f"{random.choice(SELLER_A)} {random.choice(SELLER_B)} {city}"
        while name in used:
            name = f"{random.choice(SELLER_A)} {random.choice(SELLER_B)} {city}"
        used.add(name)
        sellers[f"seller_{i:03d}"] = {
            "name": name,
            "nameLower": name.lower(),
            "city": city,
            "categories": random.sample(categories, k=random.randint(2, 3)),
            "isVerified": random.random() < 0.5,
            "followers": random.randint(50, 50_000),
            "joinedAt": NOW - timedelta(days=random.randint(60, 1500)),
            "_quality": random.uniform(0.3, 0.97),
        }
    for category in categories:  # every category needs enough sellers
        while sum(category in s["categories"] for s in sellers.values()) < 4:
            seller = random.choice(list(sellers.values()))
            if category not in seller["categories"]:
                seller["categories"].append(category)
    return sellers


def make_products(sellers: dict[str, dict]) -> dict[str, dict]:
    products, number = {}, 0
    for cid, category in CATALOG.items():
        category_sellers = [sid for sid, s in sellers.items() if cid in s["categories"]]
        for brand, model, (low, high), variants in category["items"]:
            for sid in random.sample(category_sellers, k=min(len(category_sellers), random.randint(2, 6))):
                seller = sellers[sid]
                price = demo_price(random.uniform(low, high))
                discount = random.choice([0, 0, 5, 10, 15, 20, 25, 30, 40])
                original = demo_price(price / (1 - discount / 100)) if discount else price
                name = f"{brand} {model}"
                products[f"prod_{number:04d}"] = {
                    "name": name,
                    "nameLower": name.lower(),
                    "brand": brand,
                    "model": model,
                    "category": cid,
                    "categoryName": category["name"],
                    "sellerId": sid,
                    "sellerName": seller["name"],
                    "price": price,
                    "originalPrice": original,
                    "discountPercent": discount,
                    "stock": random.choice([0, 2, 3, 5, 8, 12, 25, 40, 60, 100]),
                    "variants": variants,
                    "freeShipping": price >= FREE_SHIPPING_ABOVE or random.random() < 0.3,
                    "deliveryDays": random.randint(2, 6),
                    "description": f"{name}. Available in {', '.join(variants)}. "
                                   f"{random.choice(['Cash on delivery available.', '7 days easy return.', 'Ships from ' + seller['city'] + '.'])}",
                    "rating": 0,
                    "reviewCount": 0,
                    "soldCount": 0,
                    "isActive": True,
                    "createdAt": NOW - timedelta(days=random.randint(10, 500)),
                    "_quality": clamp(0.5 * seller["_quality"] + 0.5 * random.uniform(0.15, 1.0), 0.1, 0.98),
                }
                number += 1
    return products


def make_users() -> dict[str, dict]:
    users = {}
    for i in range(USER_COUNT):
        first = "Waseem" if i < 6 else "Ali" if i < 12 else random.choice(FIRST_NAMES)  # easy name-search tests
        last = random.choice(LAST_NAMES)
        name, city = f"{first} {last}", random.choice(CITIES)
        users[f"user_{i:03d}"] = {
            "name": name,
            "nameLower": name.lower(),
            "role": "customer",
            "city": city,
            "joinedAt": NOW - timedelta(days=random.randint(5, 900)),
            # private: MCP tools must never return these for other users
            "email": f"{first.lower()}.{last.lower()}{i}@example.com",
            "phone": f"+92 3{random.randint(0, 4)}{random.randint(0, 9)} {random.randint(1_000_000, 9_999_999)}",
            "address": random_address(city),
        }
    return users


def make_me() -> tuple[str, dict]:
    """Create (or reuse) your Firebase Auth account from .env and return your user document."""
    email = os.environ["STORE_USER_EMAIL"]
    password = os.environ["STORE_USER_PASSWORD"]
    name = os.getenv("STORE_USER_NAME", "Demo User")
    city = os.getenv("STORE_USER_CITY", "Lahore")
    try:
        user = auth.get_user_by_email(email)
        auth.update_user(user.uid, password=password, display_name=name)
    except auth.UserNotFoundError:
        user = auth.create_user(email=email, password=password, display_name=name)
    return user.uid, {
        "name": name,
        "nameLower": name.lower(),
        "role": "customer",
        "city": city,
        "joinedAt": NOW - timedelta(days=200),
        "email": email,
        "phone": "",
        "address": random_address(city),
    }


def make_reviews(products: dict[str, dict], users: dict[str, dict]) -> dict[str, dict]:
    reviews, user_ids = {}, list(users)
    for pid, product in products.items():
        stars_given = []
        for _ in range(random.choice([0, 1, 2, 3, 5, 8, 12, 15, 20, 30])):
            stars = pick_stars(product["_quality"])
            uid = random.choice(user_ids)
            reviews[f"review_{len(reviews):05d}"] = {
                "productId": pid,
                "productName": product["name"],
                "sellerId": product["sellerId"],
                "category": product["category"],
                "userId": uid,
                "userName": short_name(users[uid]["name"]),
                "rating": stars,
                "title": random.choice(TITLES[stars]),
                "comment": review_comment(product["category"], stars),
                "helpfulCount": random.randint(0, 60),
                "verifiedPurchase": random.random() < 0.8,
                "createdAt": NOW - timedelta(days=random.randint(1, 300)),
            }
            stars_given.append(stars)
        product["rating"] = round(sum(stars_given) / len(stars_given), 1) if stars_given else 0
        product["reviewCount"] = len(stars_given)
        product["soldCount"] = len(stars_given) * random.randint(3, 15) + random.randint(0, 40)
    return reviews


def make_seller_reviews(sellers: dict[str, dict], users: dict[str, dict]) -> dict[str, dict]:
    reviews, user_ids = {}, list(users)
    for sid, seller in sellers.items():
        stars_given = []
        for _ in range(random.randint(5, 30)):
            stars = pick_stars(seller["_quality"])
            uid = random.choice(user_ids)
            reviews[f"seller_review_{len(reviews):05d}"] = {
                "sellerId": sid,
                "sellerName": seller["name"],
                "userId": uid,
                "userName": short_name(users[uid]["name"]),
                "rating": stars,
                "comment": seller_comment(stars),
                "createdAt": NOW - timedelta(days=random.randint(1, 300)),
            }
            stars_given.append(stars)
        seller["rating"] = round(sum(stars_given) / len(stars_given), 1)
        seller["reviewCount"] = len(stars_given)
        seller["positivePercent"] = round(100 * sum(s >= 4 for s in stars_given) / len(stars_given))
    return reviews


def status_history(status: str, placed_at: datetime) -> list[dict]:
    """Realistic timeline of status changes for an order."""
    if status == "cancelled":
        return [{"status": "placed", "at": placed_at},
                {"status": "cancelled", "at": placed_at + timedelta(hours=random.uniform(1, 20))}]
    path = FLOW[: FLOW.index(status) + 1] if status in FLOW else FLOW + ["return_requested"]
    if status == "returned":
        path = path + ["returned"]
    history, at = [], placed_at
    for step in path:
        history.append({"status": step, "at": at})
        at += timedelta(hours=random.uniform(4, 20))
    return history


def make_order(number: int, user_id: str, user: dict, status: str, products: dict[str, dict],
               days_ago: float | None = None) -> dict:
    days_ago = days_ago if days_ago is not None else random.uniform(*AGE_DAYS[status])
    placed_at = NOW - timedelta(days=days_ago)
    picks = random.sample(list(products.items()), k=random.choice([1, 1, 1, 2, 2, 3]))

    items = []
    for pid, p in picks:
        quantity = random.choice([1, 1, 1, 2])
        items.append({
            "productId": pid, "name": p["name"], "brand": p["brand"],
            "sellerId": p["sellerId"], "sellerName": p["sellerName"],
            "variant": random.choice(p["variants"]), "quantity": quantity,
            "unitPrice": p["price"], "lineTotal": p["price"] * quantity,
        })
    subtotal = sum(i["lineTotal"] for i in items)
    free = subtotal >= FREE_SHIPPING_ABOVE or all(p["freeShipping"] for _, p in picks)
    shipping = 0 if free else SHIPPING_FEE

    history = status_history(status, placed_at)
    delivered_at = next((h["at"] for h in history if h["status"] == "delivered"), None)
    payment = random.choice(PAYMENTS)
    if status == "returned" or (status == "cancelled" and payment != "COD"):
        payment_status = "refunded"
    elif status == "cancelled":
        payment_status = "not_charged"
    else:
        payment_status = "paid" if payment != "COD" or delivered_at else "pending"
    shipped = status in ("shipped", "delivered", "returned", "return_requested")

    return {
        "orderNumber": f"EC-{number}",
        "userId": user_id,
        "userName": user["name"],
        "items": items,
        "subtotal": subtotal,
        "shippingFee": shipping,
        "total": subtotal + shipping,
        "paymentMethod": payment,
        "paymentStatus": payment_status,
        "status": status,
        "statusHistory": history,
        "shippingAddress": user["address"],
        "courier": random.choice(COURIERS) if shipped else None,
        "trackingNumber": f"TRK{random.randint(10**9, 10**10 - 1)}" if shipped else None,
        "placedAt": placed_at,
        "deliveredAt": delivered_at,
    }


def make_returns(orders: dict[str, dict]) -> dict[str, dict]:
    returns = {}
    for oid, order in orders.items():
        if order["status"] not in ("returned", "return_requested"):
            continue
        requested = next(h["at"] for h in order["statusHistory"] if h["status"] == "return_requested")
        resolved = next((h["at"] for h in order["statusHistory"] if h["status"] == "returned"), None)
        item = order["items"][0]
        returns[f"return_{len(returns):04d}"] = {
            "orderId": oid,
            "orderNumber": order["orderNumber"],
            "userId": order["userId"],
            "items": [item],
            "reason": random.choice(RETURN_REASONS),
            "status": "refunded" if order["status"] == "returned" else "requested",
            "refundAmount": item["lineTotal"],
            "requestedAt": requested,
            "resolvedAt": resolved,
        }
    return returns


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete previously seeded data first")
    args = parser.parse_args()

    db = start_firebase()
    if args.reset:
        print("Deleting old demo data...")
        delete_seeded(db)

    print("Building data...")
    categories = make_categories()
    sellers = make_sellers()
    products = make_products(sellers)
    users = make_users()
    my_id, me = make_me()
    users[my_id] = me

    reviews = make_reviews(products, {k: v for k, v in users.items() if k != my_id})
    seller_reviews = make_seller_reviews(sellers, {k: v for k, v in users.items() if k != my_id})

    orders, number = {}, 10001
    customer_ids = [uid for uid in users if uid != my_id]
    for _ in range(ORDER_COUNT):
        uid = random.choice(customer_ids)
        orders[f"order_{number}"] = make_order(number, uid, users[uid], random.choice(ORDER_STATUSES), products)
        number += 1
    my_numbers = []
    for status, days_ago in MY_ORDERS:
        orders[f"order_{number}"] = make_order(number, my_id, me, status, products, days_ago)
        my_numbers.append((f"EC-{number}", status, days_ago))
        number += 1
    returns = make_returns(orders)

    print("Writing to Firestore...")
    write_all(db, "categories", categories)
    write_all(db, "sellers", sellers)
    write_all(db, "products", products)
    write_all(db, "reviews", reviews)
    write_all(db, "seller_reviews", seller_reviews)
    write_all(db, "users", users)
    write_all(db, "orders", orders)
    write_all(db, "returns", returns)

    print(f"\nDone. Your account: {me['name']} ({my_id})")
    print("Your test orders:")
    for order_number, status, days_ago in my_numbers:
        print(f"  {order_number}  {status:<10} placed {days_ago} days ago")


if __name__ == "__main__":
    main()