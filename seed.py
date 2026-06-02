"""Sample dataset: 30+ stores across 8 categories, a shared product catalogue,
per-shop inventory (price + stock), demo users, delivery partners and reviews.

All coordinates are real points around Bengaluru, India, clustered near the
default customer location (12.9716, 77.5946) so distances/maps look realistic.
"""

import random

from models import (DeliveryPartner, Inventory, Order, OrderItem, Payment,
                    Product, Review, Shop, User)
from product_images import image_for, shop_image

# Deterministic randomness so the demo dataset is reproducible.
RNG = random.Random(42)

# --- Product catalogue, grouped by category -------------------------------
CATALOGUE = {
    "Grocery": ["Milk", "Rice", "Wheat Flour", "Sugar", "Cooking Oil", "Tea",
                "Coffee", "Salt", "Eggs", "Bread", "Biscuits", "Chips", "Soap",
                "Shampoo", "Toothpaste", "Toothbrush", "Detergent Powder",
                "Bananas", "Apples", "Tomatoes"],
    "Electronics": ["Laptop", "Bluetooth Earbuds", "Power Bank", "USB Cable",
                    "LED Bulb", "Phone Charger", "Smart Watch", "Headphones"],
    "Clothing": ["Cotton T-Shirt", "Polo T-Shirt", "Men's Casual Shirt",
                 "Women's Kurti", "Jeans", "Leggings", "Hoodie", "Track Pants",
                 "Saree", "Kids T-Shirt"],
    "Footwear": ["Running Shoes", "Sandals", "Formal Shoes", "Sneakers",
                 "Flip Flops"],
    "Stationery": ["Calculator", "Notebook", "Ball Pen", "A4 Paper",
                   "Geometry Box", "Marker", "Stapler"],
    "Hardware": ["Hammer", "Electric Drill", "Door Lock", "Screwdriver Set",
                 "Paint 1L", "Drill Machine", "Wrench", "Nails 1kg", "PVC Pipe"],
    "Sports": ["Cricket Bat", "Football", "Yoga Mat", "Dumbbell 5kg",
               "Badminton Racket", "Skipping Rope"],
    "Home Decor": ["Table Lamp", "Wall Clock", "Cushion Cover", "Photo Frame",
                   "Flower Vase", "Curtain Set", "Laptop Bag"],
}

PRICE_RANGE = {
    "Grocery": (20, 120), "Electronics": (250, 65000), "Clothing": (300, 2500),
    "Footwear": (350, 4000), "Stationery": (10, 600), "Hardware": (50, 4500),
    "Sports": (150, 3500), "Home Decor": (120, 2200),
}

# --- Real local retail shops (name, category, lat, lng, address, delivery, parking)
# Names are real Bengaluru-area shops, so the "Navigate" button (which opens a
# Google-Maps search by shop name) lands on the shop's live, real location.
STORES = [
    # Grocery
    ("ANNAPOORNESHWARI PROVISION STORE", "Grocery", 12.9726, 77.5946, "Near Market Rd, Bengaluru", True, True),
    ("Annapurna Store", "Grocery", 12.9650, 77.5990, "Brigade Road, Bengaluru", False, False),
    ("More Supermarket", "Grocery", 12.9810, 77.5900, "Commercial Street, Bengaluru", True, True),
    ("Reliance Smart Bazaar", "Grocery", 12.9600, 77.5850, "Jayanagar 4th Block, Bengaluru", True, True),

    # Electronics
    ("Reliance Digital", "Electronics", 12.9740, 77.5960, "SP Road, Bengaluru", True, True),
    ("KARAN ELECTRICALS & ELECTRONICS", "Electronics", 12.9705, 77.6010, "Church Street, Bengaluru", True, False),
    ("LAVITH ELECTRONICS AND HOME APPLIANCES", "Electronics", 12.9620, 77.5880, "Koramangala, Bengaluru", True, True),
    ("Croma", "Electronics", 12.9790, 77.5990, "Frazer Town, Bengaluru", True, True),

    # Clothing — real stores near Whitefield / Kadugodi, Bengaluru
    ("RIDDHI SIDDHI TEXTILEES", "Clothing", 12.9698, 77.7499, "Pattandur Agrahara Main Road, ITPL Main Road, Whitefield, Bengaluru 560066", True, True),
    ("Viska - Women & Kids Wear and Boutique", "Clothing", 12.9985, 77.7405, "Seegehalli-Kannamangala Road, Bengaluru 560115", True, False),
    ("Red kot Mens Fashion Channasandra", "Clothing", 12.9912, 77.7556, "CK Complex, Immadihalli Main Road, Channasandra, Bengaluru 560067", False, True),
    ("Mad Collections", "Clothing", 12.9776, 77.7503, "Immadihalli Main Road, Whitefield, Bengaluru 560066", True, False),
    ("Mahadev Textiles Jockey", "Clothing", 12.9821, 77.7338, "Nagondanahalli, Whitefield, Bengaluru 560066", False, True),
    ("Garment Ville", "Clothing", 13.0099, 77.7585, "Kadugodi-Medahalli Main Road, near Lake Montfort School, Bengaluru 560049", True, True),
    ("A Ramaiah Textiles", "Clothing", 12.9089, 77.7012, "Arehalli, Kalkunte Agrahara, Bengaluru 560117", True, False),
    ("Om Sri Khadi Bhandar", "Clothing", 12.9669, 77.7172, "AECS Layout C Block, Brookefield, Bengaluru 560037", True, True),
    ("Maruthi Clothing Company", "Clothing", 12.9788, 77.6962, "Doddanakundi Industrial Area, Whitefield Road, Bengaluru 560048", True, True),
    ("Cloth Studio", "Clothing", 13.0719, 77.7986, "Dodda Dunnasandra Cross, Hoskote, Bengaluru 560117", False, True),

    # Footwear
    ("Matha Rani Bhatiyani Footwear", "Footwear", 12.9722, 77.5975, "MG Road, Bengaluru", True, False),
    ("Fashion Footwear", "Footwear", 12.9690, 77.5905, "Jayanagar, Bengaluru", False, False),
    ("Metro Shoes", "Footwear", 12.9760, 77.6020, "HSR Layout, Bengaluru", True, True),

    # Stationery
    ("Balaji Stationery & Gifts", "Stationery", 12.9718, 77.5952, "Avenue Road, Bengaluru", True, False),
    ("Sri Bhagyalakshmi Stores Books & Stationery", "Stationery", 12.9655, 77.5940, "Gandhi Bazaar, Bengaluru", False, True),
    ("Sapna Book House", "Stationery", 12.9800, 77.5930, "Malleshwaram, Bengaluru", True, False),

    # Hardware
    ("Balaji Hardware Sanitaryware & Electricals", "Hardware", 12.9745, 77.5895, "SP Road, Bengaluru", True, True),
    ("DEV SHREE HARDWARE AND ELECTRICAL", "Hardware", 12.9610, 77.6000, "Wilson Garden, Bengaluru", False, True),
    ("Sri Vinayaka Hardware", "Hardware", 12.9805, 77.5965, "Shivajinagar, Bengaluru", True, False),

    # Sports
    ("E ZONE SPORTS", "Sports", 12.9730, 77.6030, "Koramangala, Bengaluru", True, True),
    ("R R Sports", "Sports", 12.9670, 77.5870, "Jayanagar 9th Block, Bengaluru", False, False),
    ("Decathlon", "Sports", 12.9795, 77.5910, "Rajajinagar, Bengaluru", True, True),

    # Home Decor
    ("Spark Furnishing", "Home Decor", 12.9715, 77.5985, "Richmond Road, Bengaluru", True, True),
    ("Freedom Tree Home Store, Whitefield Bengaluru", "Home Decor", 12.9645, 77.5915, "Whitefield, Bengaluru", True, True),
    ("Home Centre", "Home Decor", 12.9775, 77.6010, "CV Raman Nagar, Bengaluru", True, True),
]

DELIVERY_PARTNERS = [
    ("Ravi Kumar", "9800000001", 12.9720, 77.5950),
    ("Anjali Singh", "9800000002", 12.9680, 77.5980),
    ("Mohammed Imran", "9800000003", 12.9770, 77.5920),
    ("Suresh Reddy", "9800000004", 12.9640, 77.5900),
    ("Priya Nair", "9800000005", 12.9800, 77.6000),
]

REVIEW_COMMENTS = [
    "Great prices and fast service!", "Staff was very helpful.",
    "Product was exactly as listed.", "Quick delivery, well packed.",
    "Good quality, will buy again.", "Decent store, slightly pricey.",
    "Loved the variety available.", "Convenient and close to home.",
]


def run(db):
    # --- demo users --------------------------------------------------------
    admin = User(name="Platform Admin", email="admin@localfind.in",
                 role="admin", phone="9000000000")
    admin.set_password("password123")
    db.session.add(admin)

    customer = User(name="Demo Customer", email="customer@localfind.in",
                    role="customer", phone="9111111111",
                    lat=12.9716, lng=77.5946)
    customer.set_password("password123")
    db.session.add(customer)

    # --- a pool of customers (so customer analytics is meaningful) ---------
    customers = [customer]
    first = ["Aarav", "Diya", "Vivaan", "Ananya", "Aditya", "Ishaan", "Saanvi",
             "Kabir", "Myra", "Arjun", "Riya", "Reyansh", "Aadhya", "Vihaan",
             "Anika", "Krishna", "Navya", "Sai", "Pari", "Dhruv", "Kiara",
             "Ayaan", "Zara", "Rohan", "Tara", "Yash", "Nisha", "Karan",
             "Meera", "Veer", "Sara", "Aryan", "Ira", "Neil", "Avni"]
    for i, fn in enumerate(first, 1):
        u = User(name=f"{fn} Sharma", email=f"user{i}@localfind.in",
                 role="customer", phone=f"90000{i:05d}",
                 lat=12.9716 + RNG.uniform(-0.05, 0.05),
                 lng=77.5946 + RNG.uniform(-0.05, 0.05))
        u.set_password("password123")
        db.session.add(u)
        customers.append(u)
    db.session.flush()

    # --- products (one row per unique product name) ------------------------
    products = {}
    for category, names in CATALOGUE.items():
        for name in names:
            p = Product(name=name, category=category,
                        image=image_for(name),
                        description=f"{name} — available at local {category.lower()} stores.")
            db.session.add(p)
            products[name] = p
    db.session.flush()

    # --- shops + owners + inventory ---------------------------------------
    for idx, (name, cat, lat, lng, addr, delivery, parking) in enumerate(STORES, 1):
        owner = User(name=f"{name} Owner", email=f"owner{idx}@localfind.in",
                     role="owner", phone=f"98765{idx:05d}", lat=lat, lng=lng)
        owner.set_password("password123")
        db.session.add(owner)
        db.session.flush()

        shop = Shop(
            owner_id=owner.id, name=name, owner_name=owner.name,
            mobile=f"98765{idx:05d}", address=addr, lat=lat, lng=lng,
            category=cat, delivery_available=delivery,
            delivery_radius=RNG.choice([2, 3, 4, 5]),
            rating=round(RNG.uniform(3.6, 4.9), 1), parking=parking,
            image=shop_image(cat, name),
            verified=True,
        )
        db.session.add(shop)
        db.session.flush()

        # Stock this shop with products from its own category + a few staples.
        own = list(CATALOGUE[cat])
        staples = RNG.sample(CATALOGUE["Grocery"], 2) if cat != "Grocery" else []
        lo, hi = PRICE_RANGE[cat]
        for pname in own + staples:
            base = lo if pname in staples else None
            price = (round(RNG.uniform(20, 120))
                     if pname in staples
                     else round(RNG.uniform(lo, hi)))
            db.session.add(Inventory(
                shop_id=shop.id, product_id=products[pname].id,
                price=price,
                cost=round(price * RNG.uniform(0.55, 0.78), 2),  # margin 22–45%
                stock=RNG.choice([0, 2, 4, 8, 15, 25, 40, 60]),
                sold=0,  # accumulated from generated order history below
                views=RNG.randint(20, 800),
            ))

        # a couple of reviews per shop
        for _ in range(RNG.randint(1, 3)):
            db.session.add(Review(
                shop_id=shop.id, customer_id=customer.id,
                rating=RNG.randint(3, 5),
                comment=RNG.choice(REVIEW_COMMENTS)))

    # --- delivery partners -------------------------------------------------
    for pname, phone, plat, plng in DELIVERY_PARTNERS:
        db.session.add(DeliveryPartner(name=pname, phone=phone,
                                       lat=plat, lng=plng, available=True,
                                       rating=round(RNG.uniform(4.0, 5.0), 1)))

    db.session.commit()

    _generate_order_history(db, customers)


# ---------------------------------------------------------------------------
# Rich order history → powers the analytics / BI dashboards.
# ~750 orders spread across the last 12 months, with realistic peak-hour /
# weekend bias, status mix (completed / pending / cancelled) and co-purchases.
# ---------------------------------------------------------------------------

def _generate_order_history(db, customers):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    shops = Shop.query.all()
    inv_by_shop = {s.id: [i for i in s.inventory] for s in shops}
    methods = ["upi", "upi", "card", "cod"]

    # Hour weights → evening peak; weekday weights → busy weekends.
    hour_pool = ([9, 10, 11] + [12, 13] * 2 + [17, 18, 19, 20] * 4
                 + [21, 22] * 2 + [8, 15, 16])
    weekday_bias = [1, 1, 1, 1, 2, 3, 3]  # Mon..Sun

    n_orders = 750
    txn = 0
    for _ in range(n_orders):
        shop = RNG.choice(shops)
        invs = [i for i in inv_by_shop[shop.id]]
        if not invs:
            continue
        cust = RNG.choice(customers)

        # timestamp in last 365 days, weighted to recent + peak hours/days
        days_ago = int(abs(RNG.gauss(0, 130))) % 365
        created = now - timedelta(days=days_ago)
        # nudge weekday by bias (re-roll a few times toward weekends)
        for _ in range(2):
            if RNG.random() > weekday_bias[created.weekday()] / 3:
                created = created - timedelta(days=RNG.randint(1, 3))
        created = created.replace(hour=RNG.choice(hour_pool),
                                  minute=RNG.randint(0, 59))

        # status mix
        roll = RNG.random()
        if roll < 0.66:
            status = RNG.choice(["delivered", "collected"])       # completed
        elif roll < 0.86:
            status = RNG.choice(["placed", "placed", "accepted", "packed",
                                 "out_for_delivery"])  # pending / in-progress
        else:
            status = "cancelled"

        order_type = "delivery" if (shop.delivery_available and RNG.random() > 0.4) else "reserve"
        order = Order(customer_id=cust.id, shop_id=shop.id, order_type=order_type,
                      status=status, total=0, address="Bengaluru", created_at=created)
        db.session.add(order)
        db.session.flush()

        # 1–3 line items (co-purchases drive "frequently bought together")
        line_invs = RNG.sample(invs, k=min(len(invs), RNG.choice([1, 1, 2, 2, 3])))
        total = 0
        for inv in line_invs:
            qty = RNG.choice([1, 1, 1, 2, 2, 3])
            db.session.add(OrderItem(order_id=order.id, inventory_id=inv.id,
                                     product_name=inv.product.name,
                                     qty=qty, price=inv.price))
            total += inv.price * qty
            if status in ("delivered", "collected"):
                inv.sold = (inv.sold or 0) + qty   # only completed sales count
        order.total = round(total, 2)

        txn += 1
        db.session.add(Payment(order_id=order.id,
                               method=RNG.choice(methods), amount=order.total,
                               status="paid" if status in ("delivered", "collected") else "pending",
                               txn_ref=f"TXN{txn:06d}", created_at=created))

    # guarantee some activity *today* for the real-time counters — spread
    # across the first ~16 shops so any demo owner login sees live numbers.
    today = now
    max_hour = today.hour if today.hour >= 8 else 8
    today_plan = list(range(min(16, len(shops)))) * 2  # shops 0..15, two each
    for k in today_plan:
        shop = shops[k]
        invs = inv_by_shop[shop.id]
        if not invs:
            continue
        inv = RNG.choice(invs)
        cust = RNG.choice(customers)
        qty = RNG.choice([1, 2, 3])
        created = today.replace(hour=RNG.randint(8, max_hour),
                                minute=RNG.randint(0, 59))
        # mix that populates incoming orders + every Kanban column
        status = RNG.choice(["placed", "placed", "accepted", "packed",
                             "out_for_delivery", "delivered", "delivered"])
        order = Order(customer_id=cust.id, shop_id=shop.id,
                      order_type="delivery" if shop.delivery_available else "reserve",
                      status=status, total=round(inv.price * qty, 2),
                      address="Bengaluru", created_at=created)
        db.session.add(order)
        db.session.flush()
        db.session.add(OrderItem(order_id=order.id, inventory_id=inv.id,
                                 product_name=inv.product.name, qty=qty, price=inv.price))
        if status in ("delivered", "collected"):
            inv.sold = (inv.sold or 0) + qty
        txn += 1
        db.session.add(Payment(order_id=order.id, method="upi", amount=order.total,
                               status="paid", txn_ref=f"TXN{txn:06d}", created_at=created))

    # Lively board for the first shops (rich incoming orders + full Kanban) so
    # any demo owner login shows a populated dashboard.
    demo_states = ["placed", "placed", "placed", "accepted", "packed",
                   "out_for_delivery", "delivered"]
    for k in range(min(8, len(shops))):
        shop = shops[k]
        invs = inv_by_shop[shop.id]
        if not invs:
            continue
        for st in demo_states:
            inv = RNG.choice(invs)
            cust = RNG.choice(customers)
            qty = RNG.choice([1, 2, 3])
            created = today.replace(hour=RNG.randint(8, max_hour), minute=RNG.randint(0, 59))
            order = Order(customer_id=cust.id, shop_id=shop.id,
                          order_type=("delivery" if shop.delivery_available and RNG.random() > 0.5 else "reserve"),
                          status=st, total=round(inv.price * qty, 2),
                          address="Bengaluru", created_at=created)
            db.session.add(order)
            db.session.flush()
            db.session.add(OrderItem(order_id=order.id, inventory_id=inv.id,
                                     product_name=inv.product.name, qty=qty, price=inv.price))
            if st in ("delivered", "collected"):
                inv.sold = (inv.sold or 0) + qty
            txn += 1
            db.session.add(Payment(order_id=order.id, method=RNG.choice(["upi", "card", "cod"]),
                                   amount=order.total,
                                   status="paid" if st in ("delivered", "collected") else "pending",
                                   txn_ref=f"TXN{txn:06d}", created_at=created))

    db.session.commit()
