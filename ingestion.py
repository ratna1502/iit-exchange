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
    
    # Seeding users with passwords
    cursor.executemany('''
        INSERT OR IGNORE INTO users (user_id, roll_number, full_name, email, phone, hostel_block, room_number, user_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, '2022CSB1005', 'Rohan Sharma', '2022csb1005@iitropar.ac.in', '9876543210', 'Chenab Hostel', 'B-304', 'rohan123'),
        (2, '2023CSB1001', 'Ratna Kumari', '2023csb1001@iitropar.ac.in', '9123456789', 'Sutlej Hostel', 'A-102', 'ratna123'),
        (3, '2021EEB1040', 'Aman Verma', '2021eeb1040@iitropar.ac.in', '9988776655', 'Beas Hostel', 'C-201', 'aman123')
    ])
    
    cursor.executemany('''
        INSERT OR IGNORE INTO item_listings (item_id, seller_id, category_id, title, description, price, listing_type, daily_rental_rate, item_condition, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        (1, 1, 1, 'Hero Sprint 21-Speed Gear Bicycle', 'Good condition, new tires.', 3500.0, 'SALE', 0.0, 'GOOD', 'AVAILABLE'),
        (2, 3, 2, 'Symphony 45L Desert Air Cooler', 'Perfect for summer.', 2500.0, 'RENT', 50.0, 'LIKE_NEW', 'AVAILABLE'),
        (3, 1, 3, 'CLRS Algorithms Book (4th Ed)', 'Hardcover, clean pages.', 800.0, 'SALE', 0.0, 'LIKE_NEW', 'AVAILABLE')
    ])
    
    conn.commit()
    conn.close()
    print("Database initialized and sample data seeded successfully with security credentials!")

if __name__ == '__main__':
    setup_database()