PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE CHECK(email LIKE '%@iitropar.ac.in'),
    phone TEXT NOT NULL,
    hostel_block TEXT NOT NULL,
    room_number TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS item_listings (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK(price >= 0),
    listing_type TEXT NOT NULL CHECK(listing_type IN ('SALE', 'RENT')),
    daily_rental_rate REAL DEFAULT 0.0,
    item_condition TEXT CHECK(item_condition IN ('LIKE_NEW', 'GOOD', 'FAIR', 'WELL_USED')),
    status TEXT DEFAULT 'AVAILABLE' CHECK(status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'RENTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(seller_id) REFERENCES users(user_id),
    FOREIGN KEY(category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    final_price REAL NOT NULL,
    tx_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(item_id) REFERENCES item_listings(item_id),
    FOREIGN KEY(buyer_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_item_category ON item_listings(category_id);
CREATE INDEX IF NOT EXISTS idx_item_status ON item_listings(status);
CREATE INDEX IF NOT EXISTS idx_item_seller ON item_listings(seller_id);

CREATE TRIGGER IF NOT EXISTS update_item_status_after_sale
AFTER INSERT ON transactions
BEGIN
    UPDATE item_listings 
    SET status = 'SOLD' 
    WHERE item_id = NEW.item_id;
END;

CREATE VIEW IF NOT EXISTS active_marketplace_feed AS
SELECT 
    i.item_id,
    i.title,
    c.category_name,
    i.price,
    i.listing_type,
    i.daily_rental_rate,
    i.item_condition,
    u.full_name AS seller_name,
    u.hostel_block,
    u.room_number,
    u.email AS seller_email,
    u.phone AS seller_phone
FROM item_listings i
JOIN categories c ON i.category_id = c.category_id
JOIN users u ON i.seller_id = u.user_id
WHERE i.status = 'AVAILABLE';