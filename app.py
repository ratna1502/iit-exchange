import streamlit as st
import sqlite3
import pandas as pd

# Set Page Config with clean layout
st.set_page_config(page_title="IIT Ropar InstiMart", page_icon="🛒", layout="wide")

# Custom CSS for Premium Academic UI Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #002f6c;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    h2, h3 {
        color: #003b88;
        font-family: 'Outfit', sans-serif;
    }
    .stButton>button {
        background-color: #002f6c;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #004b93;
        color: white;
    }
    /* Metric Card Styling */
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #002f6c;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# App Connection Setup
def get_db():
    return sqlite3.connect('iit_exchange.db')

conn = get_db()

# Top Header Layout with Official Logo & Academic Title
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("iit_ropar_exchange_logo_1786387062282.jpg", width=160)
with col_title:
    st.markdown("<h1 style='margin-bottom: 0px;'>IIT ROPAR INSTIMART</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2rem; color: #666; margin-top: 5px;'>Official Campus Marketplace, Asset Rental, Bidding Engine & Student Charity Fund</p>", unsafe_allow_html=True)

st.markdown("---")

# Session state initialization for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# Sidebar Auth Console: Login & Register toggles
st.sidebar.header("🔑 Student Authentication Console")
auth_mode = st.sidebar.radio("Choose Action", ["Login", "Self Sign-Up / Register"])

if not st.session_state.logged_in:
    if auth_mode == "Login":
        login_email = st.sidebar.text_input("IIT Ropar Email", placeholder="roll_no@iitropar.ac.in").lower().strip()
        login_password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            cursor = conn.cursor()
            user_res = cursor.execute("SELECT user_id, full_name FROM users WHERE email = ? AND user_password = ?", (login_email, login_password)).fetchone()
            if user_res:
                st.session_state.logged_in = True
                st.session_state.user_id = user_res[0]
                st.session_state.user_name = user_res[1]
                st.sidebar.success(f"Welcome, {user_res[1]}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid Credentials!")
                
    elif auth_mode == "Self Sign-Up / Register":
        st.sidebar.markdown("---")
        reg_roll = st.sidebar.text_input("Roll Number (e.g. 2026DSS1048)").upper().strip()
        reg_name = st.sidebar.text_input("Full Name")
        reg_email = st.sidebar.text_input("IIT Ropar Email (@iitropar.ac.in or @iitrpr.ac.in)").lower().strip()
        reg_phone = st.sidebar.text_input("Phone Number")
        reg_hostel = st.sidebar.selectbox("Hostel Block", ["Chenab Hostel", "Sutlej Hostel", "Beas Hostel"])
        reg_room = st.sidebar.text_input("Room Number")
        reg_password = st.sidebar.text_input("Create Password", type="password")
        
        if st.sidebar.button("Register & Activate Account"):
            # Check domain pattern safely using lowercase
            if not (reg_email.endswith("@iitropar.ac.in") or reg_email.endswith("@iitrpr.ac.in")):
                st.sidebar.error("Registration Error: Only valid @iitropar.ac.in or @iitrpr.ac.in emails are allowed.")
            elif not (reg_roll and reg_name and reg_phone and reg_room and reg_password):
                st.sidebar.error("Missing Fields: All fields are required.")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO users (roll_number, full_name, email, phone, hostel_block, room_number, user_password)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (reg_roll, reg_name, reg_email, reg_phone, reg_hostel, reg_room, reg_password))
                    conn.commit()
                    st.sidebar.success("Account Created Successfully! Please switch to Login mode.")
                except Exception as e:
                    st.sidebar.error(f"Registration Failed: {e}")
else:
    st.sidebar.markdown(f"**Authenticated User:**\n{st.session_state.user_name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛍️ Browse InstiMart", 
    "➕ Post New Ad (Login Required)", 
    "⚖️ Live Bidding Panel",
    "🤝 Settle Deal", 
    "🎗️ Campus Charity Ledger"
])

with tab1:
    st.header("Active Campus Listings")
    categories = ["ALL"] + [row[0] for row in conn.cursor().execute("SELECT category_name FROM categories").fetchall()]
    category_filter = st.selectbox("Filter by Category", categories)
    
    query = "SELECT * FROM active_marketplace_feed"
    if category_filter != "ALL":
        query += f" WHERE category_name = '{category_filter}'"
        
    df_feed = pd.read_sql_query(query, conn)
    df_feed.columns = [
        "Item ID", "Title", "Category", "Base Price (₹)", "Listing Type", 
        "Rental Rate (₹/day)", "Condition", "Highest Offer (₹)", "Seller Name", 
        "Hostel Block", "Room Number", "Seller Email", "Seller Phone"
    ]
    st.dataframe(df_feed, use_container_width=True, hide_index=True)

with tab2:
    st.header("List an Asset for Sale or Rent")
    if not st.session_state.logged_in:
        st.warning("⚠️ Access Denied: Please authenticate via the Sidebar Login Console to post listings.")
    else:
        st.success(f"Authenticated as: {st.session_state.user_name}")
        with st.form("new_listing_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Item Title", placeholder="e.g. Hero Cycle, Symphony Cooler")
                category_id = st.selectbox("Category Group", [1, 2, 3, 4, 5], format_func=lambda x: {
                    1: 'Bicycles & Transport', 2: 'Room Coolers & Appliances', 
                    3: 'Textbooks & Course Material', 4: 'Electronics & Gadgets', 
                    5: 'Hostel Furniture & Decor'
                }[x])
                listing_type = st.selectbox("Type of Listing", ["SALE", "RENT"])
            with col2:
                price = st.number_input("Base Selling Price / Deposit (₹)", min_value=0.0, step=100.0, value=500.0)
                daily_rate = st.number_input("Daily Rental Rate (₹) [If RENT]", min_value=0.0, step=10.0, value=0.0)
                condition = st.selectbox("Item Condition", ["LIKE_NEW", "GOOD", "FAIR", "WELL_USED"])
                description = st.text_area("Item Details / Specifications")
                
            submit_btn = st.form_submit_button("Publish Ad")
            if submit_btn:
                if not title:
                    st.error("Title is required.")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO item_listings (seller_id, category_id, title, description, base_price, listing_type, daily_rental_rate, item_condition)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (st.session_state.user_id, category_id, title, description, price, listing_type, daily_rate, condition))
                    conn.commit()
                    st.success("Listing published successfully!")

with tab3:
    st.header("⚖️ Live Negotiation & Bidding Console")
    if not st.session_state.logged_in:
        st.warning("⚠️ Access Denied: Please authenticate to place bids on campus items.")
    else:
        col_bid_1, col_bid_2 = st.columns(2)
        with col_bid_1:
            st.subheader("Place a Higher Offer")
            with st.form("bidding_form"):
                item_id_bid = st.number_input("Item ID to Bid On", min_value=1, step=1)
                bid_amount = st.number_input("Your Bid Amount (₹)", min_value=0.0, step=50.0)
                submit_bid = st.form_submit_button("Place Bid")
                
                if submit_bid:
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO bids (item_id, buyer_id, bid_amount)
                            VALUES (?, ?, ?)
                        ''', (item_id_bid, st.session_state.user_id, bid_amount))
                        conn.commit()
                        st.success("Your bid has been recorded successfully!")
                    except Exception as e:
                        st.error(f"Failed to place bid: {e}")
        with col_bid_2:
            st.subheader("Current Active Offers Dashboard")
            query_bids = '''
                SELECT b.bid_id AS "Bid ID", i.title AS "Item Name", u.full_name AS "Bidder Name", 
                       b.bid_amount AS "Offer (₹)", b.bid_timestamp AS "Timestamp"
                FROM bids b
                JOIN item_listings i ON b.item_id = i.item_id
                JOIN users u ON b.buyer_id = u.user_id
                WHERE b.bid_status = 'PENDING'
                ORDER BY b.bid_amount DESC
            '''
            df_bids = pd.read_sql_query(query_bids, conn)
            st.dataframe(df_bids, use_container_width=True, hide_index=True)

with tab4:
    st.header("Settle Deal Ledger")
    if not st.session_state.logged_in:
        st.warning("⚠️ Access Denied: Please authenticate to confirm purchase transactions.")
    else:
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            with col1:
                item_id = st.number_input("Item ID (Listed)", min_value=1, step=1)
            with col2:
                final_price = st.number_input("Final Negotiated Price (₹)", min_value=0.0, step=50.0)
                
            transact_btn = st.form_submit_button("Execute Deal")
            if transact_btn:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO transactions (item_id, buyer_id, final_price)
                        VALUES (?, ?, ?)
                    ''', (item_id, st.session_state.user_id, final_price))
                    cursor.execute("UPDATE bids SET bid_status = 'ACCEPTED' WHERE item_id = ? AND bid_amount = ?", (item_id, final_price))
                    conn.commit()
                    st.success("Transaction executed! Database trigger successfully marked the item status as SOLD and allocated 2% for Charity Fund.")
                except Exception as e:
                    st.error(f"Execution Error: {e}")

with tab5:
    st.header("🎗️ Campus Welfare & Charity Fund Dashboard")
    st.markdown("Every successful transaction allocates **2% of the deal value** to support nearby orphanages and social welfare projects.")
    
    cursor = conn.cursor()
    total_charity = cursor.execute("SELECT SUM(charity_share_amount) FROM transactions").fetchone()[0]
    total_charity = total_charity if total_charity else 0.0
    
    st.markdown(f"""
    <div class="metric-card">
        <p style='color:#666; margin-bottom:5px; font-weight:bold;'>TOTAL CHARITY COLLECTED FROM CAMPUS DEALS</p>
        <h2 style='color:#002f6c; margin-top:0px; font-size:2.5rem;'>₹ {total_charity:.2f}</h2>
        <p style='color:#2e7d32; margin-bottom:0px; font-weight:bold;'>📍 Allocated to: Ropar Orphanage Welfare Board</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Transaction Contribution History")
    query_history = '''
        SELECT t.tx_id AS "Tx ID", i.title AS "Item Title", t.final_price AS "Deal Amount (₹)", 
               t.charity_share_amount AS "Charity Contribution (₹)", t.tx_timestamp AS "Timestamp"
        FROM transactions t
        JOIN item_listings i ON t.item_id = i.item_id
    '''
    df_history = pd.read_sql_query(query_history, conn)
    st.dataframe(df_history, use_container_width=True, hide_index=True)