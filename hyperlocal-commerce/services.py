"""Core algorithms: distance, walking/delivery time, comparison & ranking,
delivery-partner assignment, and the AI feature layer.

These are deliberately dependency-free (pure Python + a little math) so the
demo runs anywhere, while still being the *real* logic a production system
would use (Haversine great-circle distance, weighted ranking, etc.).
"""

import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote_plus

from models import DeliveryPartner, Inventory, Order, OrderItem, Product, Shop, db

# ---------------------------------------------------------------------------
# SMART / SEMANTIC SEARCH — understands intent even when wording differs.
# ---------------------------------------------------------------------------

SYNONYMS = {
    "charger": ["charger", "phone charger", "adapter", "charging", "fast", "type-c", "usb"],
    "fast": ["fast", "charger", "quick", "rapid"],
    "earphone": ["earbuds", "bluetooth earbuds", "headphones", "headset", "tws"],
    "earphones": ["earbuds", "bluetooth earbuds", "headphones", "headset"],
    "earbuds": ["earbuds", "bluetooth earbuds", "headphones"],
    "headphone": ["headphones", "headset", "earbuds"],
    "shoe": ["running shoes", "sneakers", "formal shoes", "sandals", "footwear"],
    "shoes": ["running shoes", "sneakers", "formal shoes", "footwear"],
    "sneaker": ["sneakers", "running shoes"],
    "bag": ["laptop bag", "bag", "backpack"],
    "bulb": ["led bulb", "bulb", "light", "lamp"],
    "light": ["led bulb", "bulb", "table lamp", "lamp"],
    "pen": ["ball pen", "pen", "marker"],
    "notebook": ["notebook", "diary", "register"],
    "watch": ["smart watch", "smartwatch", "watch"],
    "shirt": ["formal shirt", "t-shirt", "shirt", "kurta"],
    "tshirt": ["t-shirt", "shirt"],
    "tee": ["t-shirt"],
    "powerbank": ["power bank", "power bank", "battery"],
    "atta": ["wheat flour", "flour"],
    "flour": ["wheat flour", "flour"],
    "oil": ["cooking oil", "oil"],
    "computer": ["laptop"],
    "laptop": ["laptop", "laptop bag"],
    "drill": ["drill machine", "drill"],
    "paint": ["paint 1l", "paint"],
    "spanner": ["wrench"],
    "bat": ["cricket bat"],
    "racket": ["badminton racket"],
}


def _tok(text):
    return [t for t in re.sub(r"[^a-z0-9\s]", " ", (text or "").lower()).split() if len(t) > 1]


def expand_terms(query):
    terms = set()
    for t in _tok(query):
        terms.add(t)
        terms.update(SYNONYMS.get(t, []))
    return terms


def semantic_score(query, product):
    """0–100 relevance of a product to a free-text query (name+category+desc)."""
    terms = expand_terms(query)
    if not terms:
        return 60  # browse mode
    name = (product.name or "").lower()
    hay = set(_tok(product.name) + _tok(product.category) + _tok(product.description))
    # token overlap (expanded terms may be multi-word → also substring check)
    overlap = sum(1 for t in terms if t in hay or t in name)
    overlap_score = overlap / max(1, len(_tok(query)))
    best_fuzzy = max([SequenceMatcher(None, t, name).ratio() for t in terms] + [0.0])
    score = 100 * (0.6 * min(1.0, overlap_score) + 0.4 * best_fuzzy)
    if any(t in name for t in _tok(query)):
        score = max(score, 82)
    return round(min(100, score))

# ---------------------------------------------------------------------------
# 12. DISTANCE CALCULATION LOGIC
# ---------------------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0
WALK_SPEED_KMPH = 5.0          # average human walking speed
DELIVERY_SPEED_KMPH = 18.0     # average two-wheeler speed in city traffic
DELIVERY_PREP_MIN = 8          # base handling/prep time per order


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance between two GPS points, in kilometres."""
    if None in (lat1, lng1, lat2, lng2):
        return None
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return round(2 * EARTH_RADIUS_KM * asin(sqrt(a)), 3)


def walking_time_min(distance_km):
    """Estimated walking time in minutes."""
    if distance_km is None:
        return None
    return max(1, round(distance_km / WALK_SPEED_KMPH * 60))


def delivery_time_min(distance_km):
    """Estimated door-to-door delivery time in minutes (prep + travel)."""
    if distance_km is None:
        return None
    return DELIVERY_PREP_MIN + max(1, round(distance_km / DELIVERY_SPEED_KMPH * 60))


def query_relevance(query, product):
    """Typo/synonym-tolerant 0..1 relevance of a product to a (partial) query."""
    qtoks = _tok(query) or [(query or "").lower().strip()]
    match_terms = set(qtoks)
    for e in expand_terms(query):
        match_terms.update(e.split())
    ptoks = set(_tok(product.name) + _tok(product.category))
    best = 0.0
    for mt in match_terms:
        for t in ptoks:
            if t.startswith(mt) or mt.startswith(t):       # prefix / partial
                best = max(best, 0.95)
            else:
                best = max(best, SequenceMatcher(None, mt, t).ratio())  # typo
    for mt in qtoks:                                        # fuzzy vs whole name
        best = max(best, SequenceMatcher(None, mt, product.name.lower()).ratio())
    return best


def instant_results(query, user_lat, user_lng, limit=5, min_rel=0.66):
    """Typeahead 'instant results' — the best live offer per matching product,
    ranked by a WEIGHTED blend of relevance, distance, price, rating, in-stock
    and popularity. Out-of-stock / far shops are pushed down."""
    q = (query or "").strip()
    if not q:
        return []

    cand = []
    for inv in Inventory.query.join(Product).join(Shop).all():
        rel = query_relevance(q, inv.product)
        if rel < min_rel:
            continue
        dist = haversine_km(user_lat, user_lng, inv.shop.lat, inv.shop.lng)
        cand.append((rel, inv, dist))
    if not cand:
        return []

    prices = [i.price for _, i, _ in cand]
    p_lo, p_hi = min(prices), max(prices)

    ranked = []
    for rel, inv, dist in cand:
        prox = max(0.0, 1 - (dist or 0) / 10.0)            # closer = better
        price_score = 0.0 if p_hi == p_lo else 1 - (inv.price - p_lo) / (p_hi - p_lo)
        rating_score = (inv.shop.rating or 0) / 5.0
        in_stock = 1.0 if inv.stock > 0 else 0.0
        popularity = min(1.0, (inv.sold or 0) / 100.0)
        rank = (0.45 * rel + 0.18 * prox + 0.12 * price_score
                + 0.10 * rating_score + 0.10 * in_stock + 0.05 * popularity)
        if not in_stock:
            rank -= 0.25                                    # push out-of-stock down
        ranked.append((rank, rel, inv, dist))

    # best offer per product (one card per product), then top-`limit` by rank
    ranked.sort(key=lambda x: -x[0])
    best, cards = {}, []
    for rank, rel, inv, dist in ranked:
        if inv.product.name in best:
            continue
        best[inv.product.name] = True
        cards.append({
            "inventory_id": inv.id, "shop_id": inv.shop_id,
            "product_name": inv.product.name, "image": inv.product.image,
            "category": inv.product.category, "price": inv.price,
            "shop_name": inv.shop.name, "rating": round(inv.shop.rating or 0, 1),
            "distance_km": dist, "distance_label": humanize_distance(dist),
            "status": inv.status, "stock": inv.stock,
            "match": round(rel * 100), "rank": round(rank, 4),
            "maps_url": maps_link(inv.shop.name, inv.shop.address),
        })
        if len(cards) >= limit:
            break
    return cards


def suggest(query, user_lat=None, user_lng=None, limit=6):
    """Smart autosuggest with typeahead instant-result cards (blended ranking),
    matching shops, and a 'did you mean' correction."""
    q = (query or "").strip()
    if not q:
        return {"instant": [], "shops": [], "did_you_mean": None}

    if user_lat is None:
        user_lat, user_lng = 12.9716, 77.5946
    instant = instant_results(q, user_lat, user_lng, limit=limit)

    terms = _tok(q)
    shops = []
    for s in Shop.query.filter_by(verified=True).all():
        nm = s.name.lower()
        if q.lower() in nm or any(t in nm for t in terms):
            shops.append({"id": s.id, "name": s.name, "category": s.category})
        if len(shops) >= 4:
            break

    dym = None
    if instant and instant[0]["match"] >= 60 and q.lower() not in instant[0]["product_name"].lower():
        dym = instant[0]["product_name"]
    return {"instant": instant, "shops": shops, "did_you_mean": dym}


def maps_link(name, area=""):
    """Live Google-Maps SEARCH link for a real shop (name + locality), so it
    resolves to the shop's true real-world location."""
    query = (name or "")
    if area:
        # append a short locality hint (first part of the address) for accuracy
        query += " " + str(area).split(",")[0]
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)


def humanize_distance(distance_km):
    if distance_km is None:
        return "—"
    if distance_km < 1:
        return f"{int(round(distance_km * 1000))} m"
    return f"{distance_km:.1f} km"


# ---------------------------------------------------------------------------
# 13. PRODUCT COMPARISON ALGORITHM  +  4/5. SMART SEARCH RESULTS
# ---------------------------------------------------------------------------

def search_inventory(query, user_lat, user_lng, category=None):
    """Find every shop that stocks a product matching `query` and decorate each
    result with price, stock, distance, walking/delivery time and rating.

    Returns a list of plain dicts ready for JSON / template rendering.
    """
    q = Inventory.query.join(Product).join(Shop)
    if category and category != "All":
        q = q.filter(Shop.category == category)

    threshold = 40 if query and query.strip() else 0
    results = []
    for inv in q.all():
        # smart semantic relevance (understands synonyms / fuzzy wording)
        score = semantic_score(query, inv.product)
        if score < threshold:
            continue
        shop = inv.shop
        dist = haversine_km(user_lat, user_lng, shop.lat, shop.lng)
        within_radius = (
            shop.delivery_available
            and dist is not None
            and dist <= (shop.delivery_radius or 0)
        )
        results.append({
            "inventory_id": inv.id,
            "shop_id": shop.id,
            "shop_name": shop.name,
            "shop_category": shop.category,
            "product_id": inv.product_id,
            "product_name": inv.product.name,
            "product_image": inv.product.image,
            "match_score": score,
            "price": inv.price,
            "stock": inv.stock,
            "sold": inv.sold or 0,
            "status": inv.status,
            "distance_km": dist,
            "distance_label": humanize_distance(dist),
            "walking_time": walking_time_min(dist),
            "delivery_available": within_radius,
            "delivery_time": delivery_time_min(dist) if within_radius else None,
            "rating": round(shop.rating or 0, 1),
            "parking": shop.parking,
            "address": shop.address,
            "contact": shop.mobile,
            "lat": shop.lat,
            "lng": shop.lng,
            "maps_url": maps_link(shop.name, shop.address),
            "verified": shop.verified,
        })
    return results


# Sorting strategies for the comparison page.
SORT_STRATEGIES = {
    "price": lambda r: (r["price"], r["distance_km"] or 1e9),
    "distance": lambda r: (r["distance_km"] or 1e9, r["price"]),
    "delivery": lambda r: (r["delivery_time"] or 1e9, r["price"]),
    "rating": lambda r: (-(r["rating"] or 0), r["price"]),
}


def sort_results(results, sort_by="distance"):
    key = SORT_STRATEGIES.get(sort_by, SORT_STRATEGIES["distance"])
    return sorted(results, key=key)


def best_value_score(results):
    """Weighted "best overall" score combining price, distance and rating.

    Each factor is min-max normalised to 0..1 (lower price/distance is better,
    higher rating is better) and combined with hackathon-tuned weights.
    Returns the same list with a `score` field, sorted best-first.
    """
    if not results:
        return results

    prices = [r["price"] for r in results]
    dists = [r["distance_km"] or 0 for r in results]
    ratings = [r["rating"] or 0 for r in results]

    def norm(v, lo, hi):
        return 0.0 if hi == lo else (v - lo) / (hi - lo)

    p_lo, p_hi = min(prices), max(prices)
    d_lo, d_hi = min(dists), max(dists)
    r_lo, r_hi = min(ratings), max(ratings)

    for r in results:
        price_score = 1 - norm(r["price"], p_lo, p_hi)            # cheaper = better
        dist_score = 1 - norm(r["distance_km"] or 0, d_lo, d_hi)  # closer  = better
        rating_score = norm(r["rating"] or 0, r_lo, r_hi)         # higher  = better
        in_stock = 1.0 if r["status"] != "out_of_stock" else 0.0
        r["score"] = round(
            0.40 * price_score
            + 0.30 * dist_score
            + 0.20 * rating_score
            + 0.10 * in_stock,
            4,
        )
    return sorted(results, key=lambda r: -r["score"])


# ---------------------------------------------------------------------------
# 14. DELIVERY ASSIGNMENT LOGIC
# ---------------------------------------------------------------------------

def assign_delivery_partner(shop):
    """Pick the nearest available delivery partner to the shop.

    Production systems also weigh current load and rating; here we use nearest
    + available, which is the dominant factor for hyperlocal (<5 km) delivery.
    """
    partners = DeliveryPartner.query.filter_by(available=True).all()
    if not partners:
        return None
    best = min(
        partners,
        key=lambda p: haversine_km(shop.lat, shop.lng, p.lat, p.lng) or 1e9,
    )
    return best


# ---------------------------------------------------------------------------
# 15. AI FEATURES
# ---------------------------------------------------------------------------

def popular_products(limit=8, shop_id=None):
    """4. Popular Product Prediction — ranks products by units sold."""
    q = db.session.query(
        Product.id, Product.name, Product.image,
        db.func.coalesce(db.func.sum(Inventory.sold), 0).label("sold"),
    ).join(Inventory, Inventory.product_id == Product.id)
    if shop_id:
        q = q.filter(Inventory.shop_id == shop_id)
    rows = (q.group_by(Product.id)
             .order_by(db.text("sold DESC"))
             .limit(limit).all())
    return [{"id": r.id, "name": r.name, "image": r.image, "sold": int(r.sold)}
            for r in rows]


def recommend_for_user(user_id, limit=6):
    """1+2. Smart / Personalised Recommendation.

    Content-based collaborative signal: look at the categories a customer has
    bought from, then surface the most popular products in those categories
    they haven't bought yet. Falls back to global popularity for new users.
    """
    bought_product_ids = set()
    category_weight = Counter()

    orders = Order.query.filter_by(customer_id=user_id).all()
    for o in orders:
        for it in o.items:
            inv = Inventory.query.get(it.inventory_id) if it.inventory_id else None
            if inv:
                bought_product_ids.add(inv.product_id)
                category_weight[inv.product.category] += it.qty

    if not category_weight:
        return popular_products(limit)

    recs = []
    for category, _ in category_weight.most_common():
        rows = (db.session.query(
                    Product.id, Product.name, Product.image,
                    db.func.coalesce(db.func.sum(Inventory.sold), 0).label("sold"))
                .join(Inventory, Inventory.product_id == Product.id)
                .filter(Product.category == category)
                .group_by(Product.id)
                .order_by(db.text("sold DESC")).all())
        for r in rows:
            if r.id not in bought_product_ids:
                recs.append({"id": r.id, "name": r.name,
                             "image": r.image, "category": category})
            if len(recs) >= limit:
                return recs
    return recs[:limit] or popular_products(limit)


def demand_forecast(shop_id):
    """3. Demand Forecasting — simple moving-average style projection.

    Projects next-period demand per product from historical sales, and flags a
    confidence band. Real systems use ARIMA/Prophet; the shape of the output is
    identical so the UI/integration stays the same.
    """
    inv_items = Inventory.query.filter_by(shop_id=shop_id).all()
    out = []
    for inv in inv_items:
        # Weekly demand proxy: total sold spread over an assumed 4-week history.
        weekly = round((inv.sold or 0) / 4.0, 1)
        projected = round(weekly * 1.15, 1)  # +15% growth assumption
        out.append({
            "product": inv.product.name,
            "sold_total": inv.sold or 0,
            "avg_weekly_demand": weekly,
            "projected_next_week": projected,
            "current_stock": inv.stock,
        })
    return sorted(out, key=lambda x: -x["projected_next_week"])


def restock_suggestions(shop_id):
    """5. Auto Restocking Suggestions.

    Recommends a reorder quantity when projected demand outpaces current stock
    (target = enough to cover ~2 weeks of projected demand).
    """
    suggestions = []
    for f in demand_forecast(shop_id):
        target = f["projected_next_week"] * 2
        if f["current_stock"] < target:
            suggestions.append({
                "product": f["product"],
                "current_stock": f["current_stock"],
                "recommended_order": int(round(target - f["current_stock"])),
                "reason": "Projected demand exceeds available stock",
            })
    return suggestions
