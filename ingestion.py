import sqlite3

def setup_database():
    conn = sqlite3.connect('iit_exchange.db')
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        cursor.executescript(f.read())
        
    cursor.executemany('''
        INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (?, ?)
    ''', [
        (1, 'Bicycles & Transport'),
        (2, 'Room Coolers & Appliances'),
        (3, 'Textbooks & Course Material'),
        (4, 'Electronics & Gadgets'),
        (5, 'Hostel Furniture & Decor')
    ])
    
    # Seeding courses list (IIT Ropar Course Codes)
    cursor.executemany('''
        INSERT OR IGNORE INTO courses (course_code, course_title, department) VALUES (?, ?, ?)
    ''', [
        ('CSL201', 'Database Management Systems', 'CSE'),
        ('MAL101', 'Calculus & Linear Algebra', 'Maths'),
        ('EEL201', 'Signals and Systems', 'EE'),
        ('CSL301', 'Design and Analysis of Algorithms', 'CSE')
    ])
    
    # Seeding users with passwords
    cursor.executemany('''
        INSERT OR IGNORE INTO users (user_id, roll_number, full_name, email, phone, hostel_block, room_number, user_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, '2022CSB1005', 'Rohan Sharma', '2022csb1005@iitropar.ac.in', '9876543210', 'Chenab Hostel', 'B-304', 'rohan123'),
        (2, '2023CSB1001', 'Ratna Kumari', '2023csb1001@iitropar.ac.in', '9123456789', 'Sutlej Hostel', 'A-102', 'ratna123'),
        (3, '2021EEB1040', 'Aman Verma', '2021eeb1040@iitropar.ac.in', '9988776655', 'Beas Hostel', 'C-201', 'aman123')
    ])
    
    # Seeding items with book mapping codes
    cursor.executemany('''
        INSERT OR IGNORE INTO item_listings (item_id, seller_id, category_id, title, description, base_price, listing_type, daily_rental_rate, item_condition, status, image_url, course_mapping)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 1, 'Hero Sprint 21-Speed Gear Bicycle', 'Good condition, new tires.', 3500.0, 'SALE', 0.0, 'GOOD', 'AVAILABLE', 'https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=400&q=80', None),
        (2, 3, 2, 'Symphony 45L Desert Air Cooler', 'Perfect for summer.', 2500.0, 'RENT', 50.0, 'LIKE_NEW', 'AVAILABLE', 'https://images.unsplash.com/photo-1621259182978-f09e5e2bc090?auto=format&fit=crop&w=400&q=80', None),
        (3, 1, 3, 'Korth Database System Concepts (7th Ed)', 'Best textbook for CSL201 course project preparation. Minimal markings.', 600.0, 'SALE', 0.0, 'LIKE_NEW', 'AVAILABLE', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80', 'CSL201'),
        (4, 2, 3, 'Thomas Calculus Hardcover Textbook', 'MAL101 official reference guide. Free donation for needy juniors.', 0.0, 'BOOK_DONATION', 0.0, 'GOOD', 'AVAILABLE', 'https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?auto=format&fit=crop&w=400&q=80', 'MAL101')
    ])
    
    # Seeding initial bids
    cursor.executemany('''
        INSERT OR IGNORE INTO bids (bid_id, item_id, buyer_id, bid_amount, bid_status)
        VALUES (?, ?, ?, ?, ?)
    ''', [
        (1, 1, 2, 3600.0, 'PENDING')
    ])
    
    conn.commit()
    conn.close()
    print("Database Book Bank seeds successfully inserted!")

if __name__ == '__main__':
    setup_database()
