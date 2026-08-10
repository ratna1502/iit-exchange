PRAGMA foreign_keys = ON;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE CHECK(email LIKE '%@iitropar.ac.in' OR email LIKE '%@iitrpr.ac.in'),
    phone TEXT NOT NULL,
    hostel_block TEXT NOT NULL,
    room_number TEXT NOT NULL,
    user_password TEXT DEFAULT 'iitropar123',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

-- 3. Item Listings Table (Added image_url column)
CREATE TABLE IF NOT EXISTS item_listings (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    base_price REAL NOT NULL CHECK(base_price >= 0),
    listing_type TEXT NOT NULL CHECK(listing_type IN ('SALE', 'RENT')),
    daily_rental_rate REAL DEFAULT 0.0,
    item_condition TEXT CHECK(item_condition IN ('LIKE_NEW', 'GOOD', 'FAIR', 'WELL_USED')),
    image_url TEXT DEFAULT 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80', -- Default premium placeholder
    status TEXT DEFAULT 'AVAILABLE' CHECK(status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'RENTED')),
    allow_bids INTEGER DEFAULT 1 CHECK(allow_bids IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(seller_id) REFERENCES users(user_id),
    FOREIGN KEY(category_id) REFERENCES categories(category_id)
);

-- 4. Bids Tracking Table
CREATE TABLE IF NOT EXISTS bids (
    bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    bid_amount REAL NOT NULL,
    bid_status TEXT DEFAULT 'PENDING' CHECK(bid_status IN ('PENDING', 'ACCEPTED', 'REJECTED')),
    bid_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(item_id) REFERENCES item_listings(item_id) ON DELETE CASCADE,
    FOREIGN KEY(buyer_id) REFERENCES users(user_id),
    CHECK(bid_amount > 0)
);

-- 5. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    buyer_id INTEGER NOT NULL,
    final_price REAL NOT NULL,
    charity_share_amount REAL DEFAULT 0.0,
    tx_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(item_id) REFERENCES item_listings(item_id),
    FOREIGN KEY(buyer_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_item_category ON item_listings(category_id);
CREATE INDEX IF NOT EXISTS idx_item_status ON item_listings(status);
CREATE INDEX IF NOT EXISTS idx_bids_item ON bids(item_id);

-- TRIGGER: Automatic Status Update & 2% Charity Allocation on Sale
CREATE TRIGGER IF NOT EXISTS process_transaction_completion
AFTER INSERT ON transactions
BEGIN
    UPDATE item_listings 
    SET status = 'SOLD' 
    WHERE item_id = NEW.item_id;
    
    UPDATE transactions
    SET charity_share_amount = NEW.final_price * 0.02
    WHERE tx_id = NEW.tx_id;
END;

-- TRIGGER: Ensure new bid is higher than base price
CREATE TRIGGER IF NOT EXISTS validate_bid_amount
BEFORE INSERT ON bids
FOR EACH ROW
BEGIN
    SELECT CASE 
        WHEN NEW.bid_amount <= (SELECT base_price FROM item_listings WHERE item_id = NEW.item_id)
        THEN RAISE(ABORT, 'BID ERROR: Bid amount must be higher than the base price of the item!')
    END;
END;

-- VIEW: Marketplace Active Feed showing highest bid if any
CREATE VIEW IF NOT EXISTS active_marketplace_feed AS
SELECT 
    i.item_id,
    i.title,
    c.category_name,
    i.base_price,
    i.listing_type,
    i.daily_rental_rate,
    i.item_condition,
    i.image_url,
    COALESCE(MAX(b.bid_amount), i.base_price) AS current_highest_offer,
    u.full_name AS seller_name,
    u.hostel_block,
    u.room_number,
    u.email AS seller_email,
    u.phone AS seller_phone,
    i.status
FROM item_listings i
JOIN categories c ON i.category_id = c.category_id
JOIN users u ON i.seller_id = u.user_id
LEFT JOIN bids b ON i.item_id = b.item_id AND b.bid_status = 'PENDING'
WHERE i.status = 'AVAILABLE'
GROUP BY i.item_id;
