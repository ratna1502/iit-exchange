PRAGMA foreign_keys = ON;

-- 1. Users Table (Added user_password column for verification)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE CHECK(email LIKE '%@iitropar.ac.in'),
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

-- 3. Item Listings Table
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

-- 4. Transactions Table (Added charity_share_amount to calculate 2% automatically)
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

-- TRIGGER: Automatic Status Update & 2% Charity Allocation on Sale
CREATE TRIGGER IF NOT EXISTS process_transaction_completion
AFTER INSERT ON transactions
BEGIN
    -- Update item availability
    UPDATE item_listings 
    SET status = 'SOLD' 
    WHERE item_id = NEW.item_id;
    
    -- Calculate and allocate 2% of final price for Charity
    UPDATE transactions
    SET charity_share_amount = NEW.final_price * 0.02
    WHERE tx_id = NEW.tx_id;
END;

-- VIEW: Marketplace Active Feed
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