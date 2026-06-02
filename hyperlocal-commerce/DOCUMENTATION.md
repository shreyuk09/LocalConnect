# localConnect — Hyperlocal Commerce Platform
### Complete Project Dossier · Theme: *Retail & Local Commerce*

---

## 1. Complete Project Overview

**localConnect** is a Flask-based hyperlocal commerce platform that helps customers
discover products available in **nearby local shops in real time**. It is the
fusion of three familiar experiences:

- **Amazon** — product search, comparison, cart, payment, order tracking.
- **Google Maps** — live location, distance, routes, navigation.
- **A local business marketplace** — built to give neighbourhood retailers
  visibility and reach they don't get on national platforms.

A customer opens the app, the browser detects their GPS location, and they
search for any product (e.g. *Milk*, *Rice*, *Calculator*, *Laptop Bag*).
localConnect instantly returns every nearby shop stocking it, each annotated with
**price, live stock, distance, walking time, delivery availability + ETA, and
rating**, and lets them compare and sort by what matters (cheapest, nearest,
fastest, best rated, or an AI "best value" score). They then **reserve & collect**
or order **home delivery**, pay by UPI / Card / COD, and track fulfilment.

Shop owners register their shop, list products with prices and stock, and manage
inventory and orders from a dashboard with **AI demand forecasting and
auto-restock suggestions**. Admins verify shops and monitor the platform.

---

## 2. Problem Statement

Customers waste time and fuel physically visiting multiple stores to find a
product, compare prices and check availability — only to discover it's out of
stock. Meanwhile, **local retailers struggle with visibility and customer reach**,
losing footfall to large e-commerce players despite often having the product
in stock just streets away.

**There is no real-time, location-aware bridge between a customer who needs a
product *now* and the local shops that already have it.**

---

## 3. Objectives

1. Let customers find products in nearby shops in **real time** with live stock.
2. Show **price, distance, walking time, delivery ETA and rating** at a glance.
3. Enable **side-by-side comparison** and smart sorting/ranking.
4. Offer **reserve-&-collect** and **home-delivery** fulfilment with online payment.
5. Give local shop owners a simple **storefront, inventory and analytics** suite.
6. Use **location intelligence** (Haversine distance, routing, delivery radius).
7. Apply lightweight **AI** for recommendations, demand forecasting and restocking.
8. Provide **admin governance** (shop verification, user/order monitoring).

---

## 4. System Architecture Diagram

```
                       ┌─────────────────────────────────────────────┐
                       │                 CLIENT (Browser)             │
                       │  HTML5 · CSS3 · Bootstrap 5 · JavaScript      │
                       │  Geolocation API · Google Maps / Leaflet      │
                       └───────────────┬───────────────┬──────────────┘
                          HTTPS (pages) │               │ fetch() JSON
                                        ▼               ▼
                       ┌─────────────────────────────────────────────┐
                       │              FLASK APPLICATION (app.py)       │
                       │                                               │
                       │  Auth (Flask-Login)   Role guard (cust/owner/ │
                       │                                       admin)  │
                       │  ┌─────────────┐  ┌─────────────┐             │
                       │  │  Page routes │  │  REST /api/* │            │
                       │  └──────┬──────┘  └──────┬──────┘             │
                       │         ▼                ▼                     │
                       │  ┌──────────────────────────────────────┐     │
                       │  │  services.py  (business logic)         │    │
                       │  │  • Haversine distance / ETA            │    │
                       │  │  • Search + comparison ranking         │    │
                       │  │  • Delivery-partner assignment         │    │
                       │  │  • AI: recommend / forecast / restock  │    │
                       │  └──────────────────────────────────────┘     │
                       │         ▼  SQLAlchemy ORM (models.py)          │
                       └─────────┼─────────────────────────────────────┘
                                 ▼
                       ┌─────────────────────────────────────────────┐
                       │   DATABASE  — SQLite (dev) / MySQL (prod)     │
                       │   users · shops · products · inventory ·      │
                       │   orders · order_items · payments · reviews · │
                       │   locations · delivery_partners               │
                       └─────────────────────────────────────────────┘
```

**Pattern:** classic 3-tier (presentation → application/logic → data) with a
thin JSON API for the dynamic, map and search-as-you-type pieces.

---

## 5. Database ER Diagram

```
USERS ──────────< SHOPS ──────────< INVENTORY >────────── PRODUCTS
  │ 1           1   │ 1               │ N            1
  │                 │                 │
  │ 1               │ 1               │
  │                 ▼                 │
  │              REVIEWS              │
  │ 1              (N)                │
  │                                   │
  ▼ N                                 │
ORDERS ──< ORDER_ITEMS >──────────────┘
  │ 1  (N)          (references inventory)
  │ 1
  ├──── 1:1 ──── PAYMENTS
  │
  └──── N:1 ──── DELIVERY_PARTNERS

LOCATIONS >─── N:1 ─── USERS        (optional saved addresses)
```

**Relationships**
- A **User** (owner) owns many **Shops**; a User (customer) places many **Orders** and writes many **Reviews**.
- A **Shop** has many **Inventory** rows; each **Inventory** links one **Shop** to one **Product** with `price`, `stock`, `sold`.
- An **Order** belongs to a customer + shop, has many **Order_Items**, one **Payment**, and optionally one **Delivery_Partner**.
- A **Review** belongs to a shop and a customer (drives the shop's average rating).

---

## 6. MySQL Schema

The complete, runnable DDL lives in [`schema_mysql.sql`](schema_mysql.sql)
(10 tables with keys, indexes and foreign-key constraints). Key excerpt:

```sql
CREATE TABLE inventory (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    shop_id    INT NOT NULL,
    product_id INT NOT NULL,
    price      DOUBLE NOT NULL,
    stock      INT DEFAULT 0,
    sold       INT DEFAULT 0,
    FOREIGN KEY (shop_id)    REFERENCES shops(id)    ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX (shop_id), INDEX (product_id)
);
```

The same tables are created automatically by SQLAlchemy (`models.py`) on SQLite
for a zero-setup demo.

---

## 7. Flask Folder Structure

```
hyperlocal-commerce/
├── app.py                  # entry point: routes, auth, REST API, error handlers
├── models.py               # 10 SQLAlchemy models + password hashing
├── services.py             # distance, comparison, delivery, AI algorithms
├── seed.py                 # 30+ store sample dataset
├── config.py               # SQLite default · MySQL via DATABASE_URL · Maps key
├── schema_mysql.sql        # canonical MySQL schema
├── requirements.txt
├── README.md
├── DOCUMENTATION.md         (this file)
├── static/
│   ├── css/style.css
│   └── js/main.js           # geolocation capture, map helpers
└── templates/
    ├── base.html  index.html  login.html  register.html  error.html
    ├── customer/  dashboard search compare map checkout orders track
    ├── shop/      register dashboard
    └── admin/     dashboard
```

---

## 8. Complete UI Design

| Page | Route | Purpose |
|------|-------|---------|
| Landing | `/` | Hero search, popular products, featured shops, live stats |
| Customer Login / Register | `/login` `/register` | Auth (role select on signup) |
| Customer Dashboard | `/dashboard` | AI recommendations, nearby shops, recent orders |
| Search Results | `/search` | Smart result cards: price, stock, distance, walk, delivery, rating |
| Product Comparison | `/compare` | Sortable table + AI best-value score bar |
| Google Maps Page | `/map` | User + shop markers, info windows, navigation links |
| Checkout | `/checkout/<inv>` | Qty, fulfilment (reserve/delivery), payment method |
| Order Tracking | `/track/<id>` | Status timeline, partner info, review form |
| Shop Dashboard | `/shop` | Inventory, orders, AI insights, reviews, analytics |
| Admin Dashboard | `/admin` | Shop verification, users, orders, products, KPIs |

**Design language:** Bootstrap 5, gradient hero (indigo→blue), rounded cards with
soft shadows, colour-coded "chips" (green = in stock/delivers, amber = low, red =
out), star ratings, progress-bar score visualisation, responsive grid.

---

## 9. API Endpoints

### Pages (HTML)
| Method | Path | Auth |
|--------|------|------|
| GET/POST | `/register`, `/login` | public |
| GET | `/logout`, `/go` | login |
| GET | `/`, `/search`, `/compare`, `/map` | public |
| GET | `/dashboard`, `/orders` | customer |
| GET/POST | `/checkout/<inventory_id>` | customer |
| GET | `/track/<order_id>` | customer/admin |
| POST | `/shop/<id>/review` | customer |
| GET | `/shop`, GET/POST `/shop/register` | owner |
| POST | `/shop/product/add`, `/shop/inventory/<id>/update` | owner |
| POST | `/shop/order/<id>/<action>` | owner |
| GET | `/admin` | admin |
| POST | `/admin/shop/<id>/verify`, `/admin/user/<id>/delete` | admin |

### REST / JSON (`fetch()` from frontend)
| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/search?q=&category=&sort=` | ranked search results |
| GET | `/api/shops` | all verified shops + distance |
| GET | `/api/recommendations` | personalised products (login) |
| GET | `/api/shop/<id>/forecast` | demand forecast + restock (owner/admin) |

**Example** `GET /api/search?q=Milk&sort=price`:
```json
{ "count": 7, "results": [
  { "shop_name": "Family Store", "product_name": "Milk", "price": 28,
    "stock": 5, "status": "low_stock", "distance_label": "1.2 km",
    "walking_time": 14, "delivery_available": false, "rating": 4.3 } ] }
```

---

## 10. User Flow Diagram

```
CUSTOMER
  Open app → (Geolocation) → Search "Milk"
     → Results (price/stock/distance/walk/delivery/rating)
        → Compare & sort  ──► pick shop
           → Checkout → choose Reserve&Collect | Home Delivery
              → Pay (UPI/Card/COD) → Order placed
                 → Track status timeline → (delivered) → Review shop

SHOP OWNER
  Register → Add shop (GPS) → [admin verifies] → Add products + stock
     → Receive order → Accept/Reject → Dispatch/Deliver | Mark collected
        → View analytics + AI forecast → Restock

ADMIN
  Login → Verify shops → Manage users/products/orders → Monitor KPIs
```

---

## 11. Google Maps Integration Logic

- **Location capture** (`static/js/main.js`): `navigator.geolocation
  .getCurrentPosition()` stores `lat`/`lng` in a cookie; the server reads it in
  `current_location()` so distances are computed server-side for every page.
- **Map render** (`templates/customer/map.html`): when `GOOGLE_MAPS_API_KEY` is
  set, the Google Maps JS API plots a blue "you" marker plus a marker per shop,
  each with an **InfoWindow** (name, category, rating, distance, delivery) and a
  **navigation deep-link** `https://www.google.com/maps/dir/?api=1&destination=lat,lng`.
- **Graceful fallback:** with no key, the page loads **Leaflet + OpenStreetMap**
  tiles and reproduces the same markers/popups — so the demo always works.
- **Navigate buttons** on search/checkout/tracking open turn-by-turn directions
  in Google Maps.

---

## 12. Distance Calculation Logic

Implemented in `services.py` using the **Haversine great-circle formula**:

```
a = sin²(Δφ/2) + cos φ₁ · cos φ₂ · sin²(Δλ/2)
d = 2R · asin(√a)            R = 6371 km
```

- `haversine_km(lat1,lng1,lat2,lng2)` → kilometres between customer and shop.
- `walking_time_min = distance / 5 km/h × 60` (avg walking speed).
- `delivery_time_min = 8 min prep + distance / 18 km/h × 60` (city two-wheeler).
- `humanize_distance` → "500 m" / "1.2 km".
- Delivery is offered only when `distance ≤ shop.delivery_radius`.

---

## 13. Product Comparison Algorithm

1. **Search** (`search_inventory`): join `Inventory→Product→Shop`, `ILIKE` match
   on product name (+ optional category), decorate each row with price, stock,
   distance, walk/delivery time, rating.
2. **Sort strategies** (`SORT_STRATEGIES`): `price`, `distance`, `delivery`,
   `rating` — each a tuple key with sensible tie-breakers.
3. **Best-value score** (`best_value_score`) — min-max normalise each factor to
   0..1 and combine:

```
score = 0.40·(1−priceNorm) + 0.30·(1−distNorm) + 0.20·ratingNorm + 0.10·inStock
```

Cheaper, closer, higher-rated and in-stock offers rise to the top; the comparison
page renders the score as a progress bar and badges the winner "Best value".

---

## 14. Delivery Assignment Logic

`assign_delivery_partner(shop)`:
1. Query `delivery_partners` where `available = TRUE`.
2. Compute Haversine distance from each partner to the shop.
3. Assign the **nearest available** partner (dominant factor for sub-5 km
   hyperlocal delivery); rating/load can be layered in as secondary weights.
4. On a delivery order the partner is attached and status advances to `accepted`;
   the shop then `dispatch`es → `out_for_delivery` → `delivered`.

---

## 15. AI Features Implementation

All in `services.py` — dependency-free, with production-shaped outputs:

1. **Smart Product Recommendation** & **2. Personalised Suggestions**
   (`recommend_for_user`): content-based — derive the customer's preferred
   categories from purchase history, then surface the most popular products in
   those categories they haven't bought. New users fall back to global popularity.
2. **Demand Forecasting** (`demand_forecast`): moving-average projection of
   per-product weekly demand from historical sales, with a +15% growth band.
   (Swap in ARIMA/Prophet later — output shape stays identical.)
3. **Popular Product Prediction** (`popular_products`): ranks products by units
   sold, globally or per shop.
4. **Auto Restocking Suggestions** (`restock_suggestions`): flags products where
   projected 2-week demand exceeds current stock and recommends a reorder qty.

These power the customer "Recommended for you" strip and the shop owner's
"AI Insights" tab (forecast table + restock list + popular chips).

---

## 16. Future Scope

- Real payment gateway (Razorpay/Stripe) + UPI deep-link intents.
- Live delivery tracking on the map (WebSocket partner GPS).
- Push/SMS/WhatsApp order notifications.
- ML upgrades: collaborative filtering, Prophet forecasting, dynamic pricing.
- Multi-language & voice search; image search ("snap a product").
- Loyalty, coupons, group/bulk buying for a locality.
- Shop owner mobile app; barcode-scan inventory.
- Carbon-saving metric ("you saved X km vs. driving across town").
- Redis caching + geospatial index (PostGIS / MySQL spatial) at scale.

---

## 17. Hackathon Pitch Deck Content

**Slide 1 — Title:** *localConnect — Find any product in shops near you, instantly.*
Retail & Local Commerce.

**Slide 2 — Problem:** Customers hop between stores to find/compare/check stock;
local shops stay invisible online and lose customers to big e-commerce.

**Slide 3 — Solution:** A real-time, location-aware marketplace that shows which
nearby shop has your product — with price, stock, distance, delivery & rating —
and lets you reserve or get it delivered.

**Slide 4 — Demo flow:** Search *Milk* → compare 7 shops → "Family Store ₹28,
1.2 km" → reserve → track. (Live demo.)

**Slide 5 — How it works:** Geolocation + Haversine distance, weighted comparison
ranking, delivery-radius matching, AI forecasting. (Architecture diagram.)

**Slide 6 — Tech:** Flask · MySQL · Bootstrap 5 · Google Maps & Geolocation API ·
Flask-Login. 10-table schema, REST API, role-based modules.

**Slide 7 — AI edge:** best-value ranking, personalised recs, demand forecasting,
auto-restock — value for *both* sides of the marketplace.

**Slide 8 — Impact:** customers save time/fuel; local shops gain digital
visibility and new orders; supports the neighbourhood economy.

**Slide 9 — Business model:** small per-order commission + featured-shop listings
+ delivery fee share + premium analytics for shops.

**Slide 10 — Roadmap & ask:** payments, live tracking, ML, mobile apps. *Help us
digitise the shop next door.*

---

## 18. Winning Hackathon Presentation (Speaker Script)

> **Hook (15s):** "Last time you needed milk *right now* — how many shops did you
> call or walk to? Your neighbourhood shop probably had it. You just couldn't
> *see* that. We fix exactly that."
>
> **Problem (20s):** Customers waste time and fuel; 60M+ local Indian retailers
> are nearly invisible online. There's no real-time bridge between *need it now*
> and *the shop that has it.*
>
> **Solution + live demo (90s):** "Watch — I allow location, search *Milk*…
> instantly seven shops, sorted by best value. Fresh Mart, ₹30, 15 in stock,
> 500 m, 6-min walk, delivers in 15. I reserve it — done — and track it here."
> Then flip to the **Shop dashboard**: "Owners get inventory, orders, and AI that
> says *'reorder 20 units of Milk — demand is rising.'*"
>
> **Why we win (30s):** It's genuinely *two-sided* — real value for customers
> **and** shopkeepers. It's **fully working today**: 32 seeded shops, live
> distance maths, comparison ranking, payments, tracking, admin, and four AI
> features. And it runs with **zero setup** — `python app.py`.
>
> **Impact + close (25s):** "We save customers time, give local shops a digital
> shelf, and keep money in the neighbourhood. localConnect — *the shop next door,
> now online.* Thank you."

**Q&A prep:** scaling → geospatial index + Redis; trust → admin verification +
reviews; offline shops → 2-min onboarding + assisted listing; monetisation →
commission + listings + analytics.
