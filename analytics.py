"""Business-intelligence engine for the shop-owner & admin dashboards.

Pure computation over the ORM models — no framework coupling, so it's easy to
unit-test. Every function returns plain dicts/lists ready for templates,
Chart.js JSON, or export.

Revenue/profit are recognised on COMPLETED orders only.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from models import (Inventory, Order, OrderItem, Product, Review, Shop, User,
                    db)

COMPLETED = ("delivered", "collected")
PENDING = ("placed", "accepted", "out_for_delivery")
CANCELLED = ("rejected", "cancelled")

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _now():
    return datetime.now(timezone.utc)


def _aware(dt):
    """Normalise naive timestamps (SQLite) to aware UTC for safe comparison."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _orders(shop_id=None):
    q = Order.query
    if shop_id is not None:
        q = q.filter_by(shop_id=shop_id)
    return q.all()


def _completed(orders):
    return [o for o in orders if o.status in COMPLETED]


# ===========================================================================
# A. REVENUE ANALYTICS
# ===========================================================================

def revenue_analytics(shop_id=None):
    now = _now()
    orders = _completed(_orders(shop_id))

    def since(days):
        cut = now - timedelta(days=days)
        return round(sum(o.total for o in orders if _aware(o.created_at) >= cut), 2)

    daily = since(1)
    weekly = since(7)
    monthly = since(30)
    yearly = since(365)
    total = round(sum(o.total for o in orders), 2)

    # growth: this 30 days vs previous 30 days
    cut1, cut2 = now - timedelta(days=30), now - timedelta(days=60)
    this_m = sum(o.total for o in orders if _aware(o.created_at) >= cut1)
    prev_m = sum(o.total for o in orders
                 if cut2 <= _aware(o.created_at) < cut1)
    growth = round((this_m - prev_m) / prev_m * 100, 1) if prev_m else (100.0 if this_m else 0.0)

    return {"daily": daily, "weekly": weekly, "monthly": monthly,
            "yearly": yearly, "total": total, "growth": growth}


# ===========================================================================
# B. SALES ANALYTICS
# ===========================================================================

def sales_analytics(shop_id=None):
    orders = _orders(shop_id)
    completed = [o for o in orders if o.status in COMPLETED]
    pending = [o for o in orders if o.status in PENDING]
    cancelled = [o for o in orders if o.status in CANCELLED]
    aov = round(sum(o.total for o in completed) / len(completed), 2) if completed else 0
    return {"total_orders": len(orders), "completed": len(completed),
            "pending": len(pending), "cancelled": len(cancelled),
            "avg_order_value": aov}


# ===========================================================================
# C. PRODUCT PERFORMANCE
# ===========================================================================

def product_performance(shop_id=None, top_n=10):
    inv_q = Inventory.query
    if shop_id is not None:
        inv_q = inv_q.filter_by(shop_id=shop_id)
    items = inv_q.all()

    rows = [{
        "name": i.product.name, "category": i.product.category,
        "sold": i.sold or 0, "views": i.views or 0, "stock": i.stock,
        "price": i.price, "conversion": round((i.sold or 0) / (i.views or 1) * 100, 1),
    } for i in items]

    top_selling = sorted(rows, key=lambda r: -r["sold"])[:top_n]
    most_viewed = sorted(rows, key=lambda r: -r["views"])[:top_n]
    fastest = sorted(rows, key=lambda r: -r["conversion"])[:5]   # sold per view
    least = sorted([r for r in rows], key=lambda r: r["sold"])[:5]
    low_stock = sorted([r for r in rows if r["stock"] <= 5], key=lambda r: r["stock"])
    return {"top_selling": top_selling, "most_viewed": most_viewed,
            "fastest_selling": fastest, "least_selling": least,
            "low_stock": low_stock}


# ===========================================================================
# D. CUSTOMER ANALYTICS
# ===========================================================================

def customer_analytics(shop_id=None):
    orders = _orders(shop_id)
    by_cust = defaultdict(list)
    for o in orders:
        if o.customer_id:
            by_cust[o.customer_id].append(o)

    total = len(by_cust)
    repeat = sum(1 for v in by_cust.values() if len(v) > 1)
    now = _now()
    cut = now - timedelta(days=30)
    new = sum(1 for cid in by_cust
              if any(_aware(o.created_at) >= cut for o in by_cust[cid])
              and min(_aware(o.created_at) for o in by_cust[cid]) >= cut)
    retention = round(repeat / total * 100, 1) if total else 0

    # reviews
    rev_q = Review.query
    if shop_id is not None:
        rev_q = rev_q.filter_by(shop_id=shop_id)
    reviews = rev_q.order_by(Review.created_at.desc()).all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0

    return {"total": total, "repeat": repeat, "new": new,
            "retention": retention, "avg_rating": avg_rating,
            "review_count": len(reviews),
            "reviews": [{"rating": r.rating, "comment": r.comment,
                         "date": _aware(r.created_at).strftime("%d %b %Y")}
                        for r in reviews[:8]]}


# ===========================================================================
# E. PROFIT & SAVINGS
# ===========================================================================

def profit_savings(shop_id=None):
    orders = _completed(_orders(shop_id))
    inv_cache = {}

    def inv(id_):
        if id_ not in inv_cache:
            inv_cache[id_] = db.session.get(Inventory, id_) if id_ else None
        return inv_cache[id_]

    revenue = round(sum(o.total for o in orders), 2)
    profit = 0.0
    for o in orders:
        for it in o.items:
            i = inv(it.inventory_id)
            unit_cost = (i.cost if i and i.cost else it.price * 0.7)
            profit += (it.price - unit_cost) * it.qty
    profit = round(profit, 2)

    # current inventory holding cost
    inv_q = Inventory.query
    if shop_id is not None:
        inv_q = inv_q.filter_by(shop_id=shop_id)
    inv_items = inv_q.all()
    inventory_cost = round(sum((i.cost or i.price * 0.7) * i.stock for i in inv_items), 2)

    # smart-inventory savings model:
    #  • operational savings ≈ 4% of revenue (less stockouts/over-ordering)
    #  • waste reduction ≈ 2.5% of inventory holding cost avoided spoilage
    operational = round(revenue * 0.04, 2)
    waste_reduction = round(inventory_cost * 0.025, 2)
    inventory_savings = round(operational + waste_reduction, 2)
    margin = round(profit / revenue * 100, 1) if revenue else 0

    return {"revenue": revenue, "profit": profit, "margin": margin,
            "inventory_cost": inventory_cost, "operational_savings": operational,
            "waste_reduction": waste_reduction,
            "inventory_savings": inventory_savings}


# ===========================================================================
# F. DEMAND INSIGHTS (AI)  — builds on services.py forecasting
# ===========================================================================

def demand_insights(shop_id):
    import services
    perf = product_performance(shop_id)
    forecast = services.demand_forecast(shop_id)
    restock = services.restock_suggestions(shop_id)

    most_demanded = perf["top_selling"][0]["name"] if perf["top_selling"] else "—"
    trending = [r["name"] for r in sorted(perf["top_selling"],
                key=lambda r: -(r["conversion"]))[:3]]
    likely_out = [f["product"] for f in forecast
                  if f["current_stock"] <= f["projected_next_week"]][:5]

    month = _now().month
    season = ("Summer" if month in (3, 4, 5) else "Monsoon" if month in (6, 7, 8, 9)
              else "Winter" if month in (12, 1, 2) else "Autumn")
    return {"most_demanded": most_demanded, "trending": trending,
            "season": season, "likely_to_run_out": likely_out,
            "restock": restock[:6], "forecast": forecast[:6]}


# ===========================================================================
# G. BUSINESS RECOMMENDATIONS (AI)
# ===========================================================================

def business_recommendations(shop_id):
    perf = product_performance(shop_id)
    di = demand_insights(shop_id)
    recs = []

    for r in perf["top_selling"][:2]:
        if r["sold"] > 0:
            recs.append({"icon": "📈", "type": "Increase stock",
                         "text": f"Increase stock of high-demand “{r['name']}” "
                                 f"({r['sold']} sold). Don't risk a stockout."})
    for r in perf["least_selling"][:2]:
        recs.append({"icon": "📉", "type": "Reduce / discount",
                     "text": f"“{r['name']}” is slow-moving — reduce reorders or "
                             f"run a clearance discount to free up capital."})
    for s in di["restock"][:2]:
        recs.append({"icon": "🔁", "type": "Restock now",
                     "text": f"Restock “{s['product']}” — order ~{s['recommended_order']} "
                             f"units before it runs out."})
    fbt = frequently_bought_together(shop_id)[:2]
    for a, b, n in fbt:
        recs.append({"icon": "🧺", "type": "Bundle offer",
                     "text": f"Customers often buy “{a}” + “{b}” together ({n}×) — "
                             f"create a combo offer."})
    recs.append({"icon": "⏰", "type": "Best time to restock",
                 "text": "Restock mid-week (Tue–Wed) to be ready for the weekend "
                         "demand peak."})
    return recs


# ===========================================================================
# H. CUSTOMER PURCHASE PATTERNS
# ===========================================================================

def frequently_bought_together(shop_id=None, top=5):
    orders = _orders(shop_id)
    pair_counts = Counter()
    for o in orders:
        names = sorted({it.product_name for it in o.items})
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pair_counts[(names[i], names[j])] += 1
    return [(a, b, n) for (a, b), n in pair_counts.most_common(top) if n > 1]


def purchase_patterns(shop_id=None):
    orders = _orders(shop_id)
    hours = Counter()
    days = Counter()
    for o in orders:
        c = _aware(o.created_at)
        if c:
            hours[c.hour] += 1
            days[c.weekday()] += 1

    peak_hour = max(hours, key=hours.get) if hours else None
    peak_day = max(days, key=days.get) if days else None
    hour_series = [hours.get(h, 0) for h in range(24)]
    day_series = [days.get(d, 0) for d in range(7)]
    return {
        "peak_hour": f"{peak_hour}:00–{peak_hour+1}:00" if peak_hour is not None else "—",
        "peak_day": WEEKDAYS[peak_day] if peak_day is not None else "—",
        "hour_series": hour_series,
        "day_series": day_series,
        "frequently_bought_together": frequently_bought_together(shop_id),
    }


# ===========================================================================
# I. REAL-TIME (TODAY) METRICS
# ===========================================================================

def realtime_today(shop_id=None):
    now = _now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    orders = [o for o in _orders(shop_id) if _aware(o.created_at) >= start]
    completed = [o for o in orders if o.status in COMPLETED]
    revenue = round(sum(o.total for o in completed), 2)
    products_sold = sum(it.qty for o in completed for it in o.items)
    active_deliveries = sum(1 for o in orders
                            if o.order_type == "delivery" and o.status == "out_for_delivery")
    new_customers = len({o.customer_id for o in orders})
    return {"orders_today": len(orders), "revenue_today": revenue,
            "products_sold_today": products_sold,
            "new_customers_today": new_customers,
            "active_deliveries": active_deliveries}


# ===========================================================================
# CHART DATA  (Chart.js-ready)
# ===========================================================================

def revenue_trend(shop_id=None, days=30):
    """Daily revenue for the last `days` days → line/area chart."""
    now = _now()
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    buckets = defaultdict(float)
    for o in _completed(_orders(shop_id)):
        c = _aware(o.created_at)
        if c >= start:
            buckets[c.strftime("%Y-%m-%d")] += o.total
    labels, data = [], []
    for i in range(days):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append((start + timedelta(days=i)).strftime("%d %b"))
        data.append(round(buckets.get(d, 0), 2))
    return {"labels": labels, "data": data}


def category_distribution(shop_id=None):
    """Sales (revenue) by product category → pie chart."""
    cat = defaultdict(float)
    for o in _completed(_orders(shop_id)):
        for it in o.items:
            inv = db.session.get(Inventory, it.inventory_id) if it.inventory_id else None
            c = inv.product.category if inv else "Other"
            cat[c] += it.price * it.qty
    return {"labels": list(cat.keys()),
            "data": [round(v, 2) for v in cat.values()]}


def chart_data(shop_id=None):
    perf = product_performance(shop_id)
    cust = customer_analytics(shop_id)
    inv_q = Inventory.query
    if shop_id is not None:
        inv_q = inv_q.filter_by(shop_id=shop_id)
    inv_items = inv_q.all()

    return {
        # Bar: top 10 most purchased
        "top_products": {
            "labels": [r["name"] for r in perf["top_selling"]],
            "data": [r["sold"] for r in perf["top_selling"]],
        },
        # Pie: category sales distribution
        "category": category_distribution(shop_id),
        # Line + Area: revenue trend
        "revenue_trend": revenue_trend(shop_id, 30),
        # Doughnut: customer segmentation
        "customer_segments": {
            "labels": ["Repeat", "New", "One-time"],
            "data": [cust["repeat"], cust["new"],
                     max(0, cust["total"] - cust["repeat"] - cust["new"])],
        },
        # Inventory: available vs sold (top 8 by sold)
        "inventory": {
            "labels": [i.product.name for i in sorted(inv_items, key=lambda x: -(x.sold or 0))[:8]],
            "stock": [i.stock for i in sorted(inv_items, key=lambda x: -(x.sold or 0))[:8]],
            "sold": [(i.sold or 0) for i in sorted(inv_items, key=lambda x: -(x.sold or 0))[:8]],
        },
        # Profit analysis: revenue vs profit vs cost per category
        "profit": _profit_by_category(shop_id),
    }


def _profit_by_category(shop_id=None):
    rev = defaultdict(float)
    prof = defaultdict(float)
    for o in _completed(_orders(shop_id)):
        for it in o.items:
            inv = db.session.get(Inventory, it.inventory_id) if it.inventory_id else None
            c = inv.product.category if inv else "Other"
            unit_cost = (inv.cost if inv and inv.cost else it.price * 0.7)
            rev[c] += it.price * it.qty
            prof[c] += (it.price - unit_cost) * it.qty
    labels = list(rev.keys())
    return {"labels": labels,
            "revenue": [round(rev[c], 2) for c in labels],
            "profit": [round(prof[c], 2) for c in labels]}


# ===========================================================================
# FULL BUNDLES
# ===========================================================================

def shop_dashboard_data(shop_id):
    return {
        "revenue": revenue_analytics(shop_id),
        "sales": sales_analytics(shop_id),
        "performance": product_performance(shop_id),
        "customers": customer_analytics(shop_id),
        "profit": profit_savings(shop_id),
        "demand": demand_insights(shop_id),
        "recommendations": business_recommendations(shop_id),
        "patterns": purchase_patterns(shop_id),
        "today": realtime_today(shop_id),
        "charts": chart_data(shop_id),
    }


# ===========================================================================
# ADMIN / PLATFORM ANALYTICS
# ===========================================================================

def admin_dashboard_data():
    shops = Shop.query.all()
    orders = Order.query.all()
    completed = _completed(orders)

    # popular shops by revenue
    shop_rev = defaultdict(float)
    for o in completed:
        shop_rev[o.shop_id] += o.total
    popular_shops = sorted(
        [{"name": s.name, "category": s.category,
          "revenue": round(shop_rev.get(s.id, 0), 2),
          "rating": s.rating} for s in shops],
        key=lambda r: -r["revenue"])[:8]

    # popular products platform-wide
    prod_sold = defaultdict(int)
    for o in completed:
        for it in o.items:
            prod_sold[it.product_name] += it.qty
    popular_products = sorted(
        [{"name": n, "sold": q} for n, q in prod_sold.items()],
        key=lambda r: -r["sold"])[:10]

    # geographic distribution (by area parsed from address)
    geo = defaultdict(float)
    for o in completed:
        shop = next((s for s in shops if s.id == o.shop_id), None)
        if shop:
            area = _area_of(shop.address)
            geo[area] += o.total
    geo_sorted = sorted(geo.items(), key=lambda kv: -kv[1])[:10]

    return {
        "stats": {
            "shops": len(shops),
            "customers": User.query.filter_by(role="customer").count(),
            "orders": len(orders),
            "revenue": round(sum(o.total for o in completed), 2),
            "completed": len(completed),
        },
        "popular_shops": popular_shops,
        "popular_products": popular_products,
        "geo": {"labels": [a for a, _ in geo_sorted],
                "data": [round(v, 2) for _, v in geo_sorted]},
        "category": category_distribution(None),
        "revenue_trend": revenue_trend(None, 30),
        "shop_markers": [{"name": s.name, "lat": s.lat, "lng": s.lng,
                          "revenue": round(shop_rev.get(s.id, 0), 2)} for s in shops],
    }


def _area_of(address):
    if not address:
        return "Unknown"
    first = address.split(",")[0].strip()
    # drop leading street number
    parts = first.split(" ", 1)
    return parts[1] if len(parts) > 1 and parts[0].rstrip(".").isdigit() else first
