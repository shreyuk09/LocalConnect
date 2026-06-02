"""Database models for the Hyperlocal Commerce platform.

Tables map directly to the requested schema:
Users, Shops, Products, Inventory, Orders, Order_Items, Payments, Reviews,
plus Delivery_Partners. (Location data is embedded on Users/Shops as lat/lng,
which is the practical equivalent of a separate Locations table.)
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def _now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    # role: customer | owner | admin
    role = db.Column(db.String(20), nullable=False, default="customer")
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=_now)

    shops = db.relationship("Shop", backref="owner", lazy=True)
    orders = db.relationship("Order", backref="customer", lazy=True)
    reviews = db.relationship("Review", backref="customer", lazy=True)

    def set_password(self, password):
        # pbkdf2 works on every Python build (scrypt needs OpenSSL extras that
        # aren't always compiled in, e.g. some 3.9 installs).
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Shop(db.Model):
    __tablename__ = "shops"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(150), nullable=False, index=True)
    owner_name = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    address = db.Column(db.String(255))
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), index=True)
    delivery_available = db.Column(db.Boolean, default=False)
    delivery_radius = db.Column(db.Float, default=3.0)  # km
    rating = db.Column(db.Float, default=4.0)
    parking = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_now)

    inventory = db.relationship("Inventory", backref="shop", lazy=True,
                                cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="shop", lazy=True)
    reviews = db.relationship("Review", backref="shop", lazy=True)


class Product(db.Model):
    """Global product catalogue. A product can be stocked by many shops."""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(50), index=True)
    image = db.Column(db.String(255))
    description = db.Column(db.String(500))

    inventory = db.relationship("Inventory", backref="product", lazy=True)


class Inventory(db.Model):
    """A specific product offered by a specific shop (price + stock)."""
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, default=0)     # wholesale/purchase cost → profit calc
    stock = db.Column(db.Integer, default=0)
    sold = db.Column(db.Integer, default=0)   # used by AI popularity features
    views = db.Column(db.Integer, default=0)  # product page views (analytics)

    LOW_STOCK_THRESHOLD = 5

    @property
    def status(self):
        if self.stock <= 0:
            return "out_of_stock"
        if self.stock <= self.LOW_STOCK_THRESHOLD:
            return "low_stock"
        return "in_stock"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"))
    # type: reserve | delivery
    order_type = db.Column(db.String(20), default="reserve")
    # status: placed | accepted | rejected | out_for_delivery | delivered | collected
    status = db.Column(db.String(30), default="placed")
    total = db.Column(db.Float, default=0)
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=_now)

    items = db.relationship("OrderItem", backref="order", lazy=True,
                            cascade="all, delete-orphan")
    payment = db.relationship("Payment", backref="order", uselist=False,
                              cascade="all, delete-orphan")
    delivery_partner_id = db.Column(db.Integer,
                                    db.ForeignKey("delivery_partners.id"))


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"))
    product_name = db.Column(db.String(150))
    qty = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    # method: upi | card | cod
    method = db.Column(db.String(20))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default="pending")  # pending | paid
    txn_ref = db.Column(db.String(60))
    created_at = db.Column(db.DateTime, default=_now)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=_now)


class DeliveryPartner(db.Model):
    __tablename__ = "delivery_partners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    available = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=4.5)

    orders = db.relationship("Order", backref="delivery_partner", lazy=True)
