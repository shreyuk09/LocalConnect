-- ===========================================================================
-- localConnect — Hyperlocal Commerce Platform · MySQL Schema
-- ---------------------------------------------------------------------------
-- The app runs on SQLite out of the box (zero setup). To use MySQL instead,
-- create this schema and set:
--   export DATABASE_URL="mysql+pymysql://user:pass@localhost/hyperlocal"
--   pip install pymysql
-- (SQLAlchemy in models.py creates equivalent tables automatically; this file
--  is the canonical reference / for manual provisioning.)
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS hyperlocal
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hyperlocal;

CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('customer','owner','admin') NOT NULL DEFAULT 'customer',
    lat           DOUBLE,
    lng           DOUBLE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shops (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    owner_id           INT,
    name               VARCHAR(150) NOT NULL,
    owner_name         VARCHAR(120),
    mobile             VARCHAR(20),
    address            VARCHAR(255),
    lat                DOUBLE NOT NULL,
    lng                DOUBLE NOT NULL,
    category           VARCHAR(50),
    delivery_available BOOLEAN DEFAULT FALSE,
    delivery_radius    DOUBLE DEFAULT 3.0,
    rating             DOUBLE DEFAULT 4.0,
    parking            BOOLEAN DEFAULT FALSE,
    image              VARCHAR(255),
    verified           BOOLEAN DEFAULT FALSE,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX (name), INDEX (category),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    category    VARCHAR(50),
    image       VARCHAR(255),
    description VARCHAR(500),
    INDEX (name), INDEX (category)
);

-- Locations: lat/lng are denormalised onto users & shops for fast distance
-- maths; this table is available for richer multi-address use-cases.
CREATE TABLE locations (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT,
    label     VARCHAR(80),
    address   VARCHAR(255),
    lat       DOUBLE NOT NULL,
    lng       DOUBLE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

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

CREATE TABLE delivery_partners (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(120),
    phone     VARCHAR(20),
    lat       DOUBLE,
    lng       DOUBLE,
    available BOOLEAN DEFAULT TRUE,
    rating    DOUBLE DEFAULT 4.5
);

CREATE TABLE orders (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT,
    shop_id             INT,
    order_type          ENUM('reserve','delivery') DEFAULT 'reserve',
    status              VARCHAR(30) DEFAULT 'placed',
    total               DOUBLE DEFAULT 0,
    address             VARCHAR(255),
    delivery_partner_id INT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)         REFERENCES users(id),
    FOREIGN KEY (shop_id)             REFERENCES shops(id),
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery_partners(id)
);

CREATE TABLE order_items (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    order_id     INT NOT NULL,
    inventory_id INT,
    product_name VARCHAR(150),
    qty          INT DEFAULT 1,
    price        DOUBLE,
    FOREIGN KEY (order_id)     REFERENCES orders(id)    ON DELETE CASCADE,
    FOREIGN KEY (inventory_id) REFERENCES inventory(id)
);

CREATE TABLE payments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT NOT NULL,
    method     ENUM('upi','card','cod'),
    amount     DOUBLE,
    status     ENUM('pending','paid') DEFAULT 'pending',
    txn_ref    VARCHAR(60),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    shop_id     INT NOT NULL,
    customer_id INT,
    rating      INT DEFAULT 5,
    comment     VARCHAR(500),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id)     REFERENCES shops(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES users(id)
);
