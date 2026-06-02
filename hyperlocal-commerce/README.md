# 🛒 localConnect — Hyperlocal Commerce Platform

> **Theme:** Retail & Local Commerce
> *"Find any product in shops near you — instantly."* — Amazon × Google Maps, built for your neighbourhood.

localConnect is a Flask web app that connects customers with nearby local shops in
real time. Search a product and instantly compare **price, live stock, distance,
walking time, delivery availability/ETA and shop rating** across stores — then
**reserve & collect** or get **home delivery**, pay by UPI / Card / COD, and
track the order. Shop owners get an inventory + analytics dashboard with AI
demand forecasting; admins verify shops and monitor the platform.

---

## ⚡ Quick start (zero config)

```bash
cd hyperlocal-commerce
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. On first run the database is auto-created
(SQLite) and **seeded with 32 shops, 57 products and 291 inventory rows**.

### Demo logins (password: `password123`)

| Role | Email |
|------|-------|
| Customer | `customer@localfind.in` |
| Shop owner | `owner1@localfind.in` (… up to `owner32`) |
| Admin | `admin@localfind.in` |

---

## 🗺️ Maps & location

* The browser asks for your **GPS location** (Geolocation API) and stores it in a
  cookie so every page computes **real distances** to shops.
* The map page uses the **Google Maps JavaScript API** when a key is set, and
  automatically falls back to **Leaflet + OpenStreetMap** when it isn't — so the
  demo works with no key and no internet billing.

```bash
export GOOGLE_MAPS_API_KEY="your-key"   # optional
```

## 🐬 Using MySQL instead of SQLite

```bash
pip install pymysql
mysql < schema_mysql.sql
export DATABASE_URL="mysql+pymysql://user:pass@localhost/hyperlocal"
python app.py
```

---

## 🧩 Features

**Customer:** registration/login · GPS location · product search · smart results
(price, stock, distance, walk time, delivery ETA, rating) · comparison + sorting
(price / nearest / fastest delivery / highest rated / **best-value AI score**) ·
maps with navigation · reserve-&-collect or delivery · UPI/Card/COD payment ·
order tracking · reviews.

**Shop owner:** shop registration (GPS capture) · product & inventory management ·
low/out-of-stock alerts · order accept/reject/dispatch/deliver · analytics
(orders, revenue, popular products, reviews) · **AI demand forecast + auto-restock**.

**Admin:** verify shops · manage users · view products/orders · platform KPIs.

**AI:** smart recommendation, personalised suggestions, demand forecasting,
popular-product prediction, auto-restock suggestions (`services.py`).

See **DOCUMENTATION.md** for the full design dossier — architecture, ER diagram,
API reference, algorithms, AI implementation, user flows, future scope and the
hackathon pitch deck.

## 📁 Structure

```
hyperlocal-commerce/
├── app.py            # Flask app: all routes, auth, REST API
├── models.py         # SQLAlchemy models (10 tables)
├── services.py       # distance, comparison, delivery & AI algorithms
├── seed.py           # 30+ stores sample dataset
├── config.py         # config (SQLite default / MySQL via DATABASE_URL)
├── schema_mysql.sql  # MySQL schema
├── requirements.txt
├── static/{css,js}/
└── templates/{customer,shop,admin}/
```
