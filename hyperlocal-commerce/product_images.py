"""Real product & shop images for the catalogue.

Every product/shop maps to a real, relevant photo via a precise keyword search
(LoremFlickr) with a stable per-item `lock`, so:
  • the image always matches the right product (keyword-based),
  • it never 404s (unlike specific CDN file paths), and
  • it never flickers/changes between reloads (locked).
"""

# Precise image keyword(s) per product → guarantees the correct subject.
KEYWORDS = {
    # Grocery
    "Milk": "milk,bottle", "Rice": "rice,grain", "Wheat Flour": "wheat,flour",
    "Sugar": "sugar", "Cooking Oil": "cooking,oil,bottle", "Tea": "tea,leaves",
    "Coffee": "coffee,beans", "Salt": "salt", "Eggs": "eggs", "Bread": "bread,loaf",
    "Biscuits": "biscuits,cookies", "Chips": "potato,chips", "Soap": "soap,bar",
    "Shampoo": "shampoo,bottle", "Toothpaste": "toothpaste", "Toothbrush": "toothbrush",
    "Detergent Powder": "detergent,laundry", "Bananas": "bananas", "Apples": "apples",
    "Tomatoes": "tomatoes",
    # Electronics
    "Laptop": "laptop,computer", "Bluetooth Earbuds": "earbuds,wireless",
    "Power Bank": "power,bank,battery", "USB Cable": "usb,cable",
    "LED Bulb": "led,bulb,light", "Phone Charger": "phone,charger",
    "Smart Watch": "smartwatch", "Headphones": "headphones",
    # Clothing
    "Cotton T-Shirt": "tshirt,cotton", "Polo T-Shirt": "polo,shirt",
    "Men's Casual Shirt": "mens,shirt", "Women's Kurti": "kurti,indian,dress",
    "Jeans": "jeans,denim", "Leggings": "leggings", "Hoodie": "hoodie,sweatshirt",
    "Track Pants": "track,pants", "Saree": "saree,sari", "Kids T-Shirt": "kids,tshirt",
    # Footwear
    "Running Shoes": "running,shoes", "Sandals": "sandals",
    "Formal Shoes": "leather,formal,shoes", "Sneakers": "sneakers", "Flip Flops": "flip,flops",
    # Stationery
    "Calculator": "calculator", "Notebook": "notebook,diary", "Ball Pen": "pen,ballpoint",
    "A4 Paper": "paper,stack", "Geometry Box": "geometry,compass", "Marker": "marker,pen",
    "Stapler": "stapler",
    # Hardware
    "Hammer": "hammer,tool", "Electric Drill": "drill,power,tool", "Door Lock": "door,lock",
    "Screwdriver Set": "screwdriver,tools", "Paint 1L": "paint,can", "Drill Machine": "drill,machine",
    "Wrench": "wrench,spanner", "Nails 1kg": "nails,hardware", "PVC Pipe": "pvc,pipe",
    # Sports
    "Cricket Bat": "cricket,bat", "Football": "football,soccer", "Yoga Mat": "yoga,mat",
    "Dumbbell 5kg": "dumbbell,weights", "Badminton Racket": "badminton,racket",
    "Skipping Rope": "skipping,rope",
    # Home Decor
    "Table Lamp": "table,lamp", "Wall Clock": "wall,clock", "Cushion Cover": "cushion,pillow",
    "Photo Frame": "photo,frame", "Flower Vase": "flower,vase", "Curtain Set": "curtains",
    "Laptop Bag": "laptop,bag",
}

SHOP_KEYWORDS = {
    "Grocery": "grocery,supermarket", "Electronics": "electronics,store,gadgets",
    "Clothing": "clothing,store,boutique", "Footwear": "shoes",
    "Stationery": "stationery,bookstore", "Hardware": "hammer",
    "Sports": "sports", "Home Decor": "wall,painting",
}


# Curated, verified real storefront photos (Unsplash CDN) for these categories.
def _u(id_):
    return f"https://images.unsplash.com/{id_}?w=600&q=80&auto=format&fit=crop"

SHOP_IMAGE_POOL = {
    # Sports keeps the curated real-photo pool; the others use keyword matches
    # below (shoes / hammer / wall paintings) for an exact subject.
    "Sports": [_u("photo-1517649763962-0c623066013b"), _u("photo-1571902943202-507ec2618e8f"),
               _u("photo-1530549387789-4c1017266635"), _u("photo-1461896836934-ffe607ba8211"),
               _u("photo-1534438327276-14e5300c3a48")],
}


def _slug(name):
    return KEYWORDS.get(name, name.lower().replace(" ", ","))


def _lock(text):
    # deterministic → same item always shows the same photo (no flicker)
    return sum(ord(c) for c in text) % 95 + 1


def image_for(name):
    return f"https://loremflickr.com/600/400/{_slug(name)}?lock={_lock(name)}"


def shop_image(category, seed=""):
    """Category-appropriate storefront photo. `seed` (e.g. the shop name) varies
    the choice so each shop in a category gets a distinct but on-theme image."""
    pool = SHOP_IMAGE_POOL.get(category)
    if pool:
        return pool[_lock(category + seed) % len(pool)]
    kw = SHOP_KEYWORDS.get(category, "shop,store")
    return f"https://loremflickr.com/600/400/{kw}?lock={_lock(category + seed)}"
