import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="IIT-Exchange Marketplace", layout="wide")

st.title("🛒 IIT-Exchange: IIT Ropar Campus Marketplace & Rental Portal")
st.markdown("*Exclusive Peer-to-Peer Marketplace for IIT Ropar Students*")

def get_db():
    return sqlite3.connect('iit_exchange.db')

conn = get_db()

tab1, tab2, tab3 = st.tabs(["🛍️ Browse Marketplace Feed", "➕ Post New Listing", "🤝 Buy / Rent Item"])

with tab1:
    st.header("Live Campus Listings")
    category_filter = st.selectbox("Filter by Category", ["ALL"] + [row[0] for row in conn.cursor().execute("SELECT category_name FROM categories").fetchall()])
    
    query = "SELECT * FROM active_marketplace_feed"
    if category_filter != "ALL":
        query += f" WHERE category_name = '{category_filter}'"
        
    df_feed = pd.read_sql_query(query, conn)
    st.dataframe(df_feed, use_container_width=True)

with tab2:
    st.header("Post an Item for Sale or Rent")
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Your IIT Ropar Email (@iitropar.ac.in)")
        title = st.text_input("Item Title (e.g. Hero Bicycle, Symphony Cooler)")
        category_id = st.selectbox("Category", [1, 2, 3, 4, 5], format_func=lambda x: {1: 'Bicycles', 2: 'Coolers/Appliances', 3: 'Books', 4: 'Electronics', 5: 'Furniture'}[x])
        listing_type = st.selectbox("Listing Type", ["SALE", "RENT"])
        
    with col2:
        price = st.number_input("Price / Deposit (₹)", min_value=0.0, value=500.0)
        daily_rate = st.number_input("Daily Rental Rate (₹) [If for Rent]", min_value=0.0, value=0.0)
        condition = st.selectbox("Condition", ["LIKE_NEW", "GOOD", "FAIR", "WELL_USED"])
        description = st.text_area("Item Description")

    if st.button("Publish Listing"):
        if not email.endswith("@iitropar.ac.in"):
            st.error("Access Denied: Only valid @iitropar.ac.in emails are authorized to post.")
        elif not title:
            st.error("Please enter a title for your item.")
        else:
            cursor = conn.cursor()
            user_res = cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
            
            if not user_res:
                st.error("User email not found in student register.")
            else:
                seller_id = user_res[0]
                cursor.execute('''
                    INSERT INTO item_listings (seller_id, category_id, title, description, price, listing_type, daily_rental_rate, item_condition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (seller_id, category_id, title, description, price, listing_type, daily_rate, condition))
                conn.commit()
                st.success("Listing published successfully to IIT-Exchange Feed!")

with tab3:
    st.header("Complete a Purchase Transaction")
    col1, col2 = st.columns(2)
    with col1:
        item_id = st.number_input("Enter Item ID to Purchase", min_value=1, value=1)
        buyer_id = st.number_input("Your Buyer User ID", min_value=1, value=2)
        final_price = st.number_input("Agreed Final Amount (₹)", min_value=0.0, value=3500.0)
        
    with col2:
        if st.button("Execute Transaction"):
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (item_id, buyer_id, final_price)
                    VALUES (?, ?, ?)
                ''', (item_id, buyer_id, final_price))
                conn.commit()
                st.success("Transaction Completed! Listing automatically marked as SOLD by Database Trigger.")
            except Exception as e:
                st.error(f"Transaction Failed: {e}")