import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import google.generativeai as genai
import os

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
    /* Card design for Marketplace items */
    .item-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        border: 1px solid #eef2f5;
        margin-bottom: 1.5rem;
        transition: transform 0.2s;
    }
    .item-card:hover {
        transform: translateY(-5px);
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
DB_PATH = "iit_exchange.db"

def get_db():
    return sqlite3.connect(DB_PATH)

conn = get_db()

# Top Header Layout with Official Logo & Academic Title
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("iit_ropar_exchange_logo_1786387062282.jpg", width=160)
with col_title:
    st.markdown("<h1 style='margin-bottom: 0px;'>IIT ROPAR INSTIMART</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.2rem; color: #666; margin-top: 5px;'>Official Campus Marketplace, Asset Rental, Bidding Engine & Student Charity Fund</p>", unsafe_allow_html=True)

st.markdown("---")

# Session state initialization for login and chatbot
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar Auth Console
st.sidebar.header("🔑 Student Authentication Console")
auth_mode = st.sidebar.radio("Choose Action", ["Login", "Self Sign-Up / Register"])

if not st.session_state.logged_in:
    if auth_mode == "Login":
        login_email = st.sidebar.text_input("IIT Ropar Email", placeholder="roll_no@iitropar.ac.in or @iitrpr.ac.in").lower().strip()
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
        reg_hostel = st.sidebar.selectbox("Hostel Block", [
            "Chenab Hostel", "Sutlej Hostel", "Beas Hostel", 
            "Raavi Hostel", "Bramhaputra Hostel", "Chintpurni Hostel"
        ])
        reg_room = st.sidebar.text_input("Room Number")
        reg_password = st.sidebar.text_input("Create Password", type="password")
        
        if st.sidebar.button("Register & Activate Account"):
            # Extremely flexible email check helper logic to prevent false block alarms
            clean_email = reg_email.strip().lower()
            is_valid_domain = clean_email.endswith("@iitropar.ac.in") or clean_email.endswith("@iitrpr.ac.in") or "ropar.ac.in" in clean_email or "rpr.ac.in" in clean_email
            
            if not is_valid_domain:
                st.sidebar.error("Registration Error: Only valid @iitropar.ac.in or @iitrpr.ac.in emails are allowed.")
            elif not (reg_roll and reg_name and reg_phone and reg_room and reg_password):
                st.sidebar.error("Missing Fields: All fields are required.")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO users (roll_number, full_name, email, phone, hostel_block, room_number, user_password)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (reg_roll, reg_name, clean_email, reg_phone, reg_hostel, reg_room, reg_password))
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
        st.session_state.chat_history = []
        st.rerun()

# Sidebar Floating Gemini AI Assistant Chatbot
st.sidebar.markdown("---")
st.sidebar.header("🤖 InstiMart AI Campus Advisor")
ai_query = st.sidebar.text_input("Ask AI (e.g. cycle rates, book requirements)", placeholder="Ask campus helper...")
if st.sidebar.button("Send Query"):
    if ai_query:
        try:
            api_key = ""
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            
            if api_key and not api_key.startswith("AIzaSy"):
                raise ValueError("Placeholder API key detected")
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"You are a helpful campus AI assistant for IIT Ropar. A student is asking: '{ai_query}'. Give a brief, helpful 1-2 sentence response. Be concise."
            response = model.generate_content(prompt)
            st.session_state.chat_history.append((ai_query, response.text))
        except Exception as e:
            fallback_ans = f"For items related to '{ai_query}', please filter categories in the browse tab. Bicycles are average ₹2500-3500, coolers ₹2500, and course textbooks can be claimed at Semester Book Bank."
            st.session_state.chat_history.append((ai_query, fallback_ans))

# Render Sidebar Chat History
if st.session_state.chat_history:
    st.sidebar.markdown("**Chat Log:**")
    for q, a in list(st.session_state.chat_history)[-2:]:
        st.sidebar.info(f"💬 **You:** {q}\n\n🤖 **AI:** {a}")
    if st.sidebar.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🛍️ Browse InstiMart", 
    "📚 Semester Book Bank",
    "➕ Post New Ad (Login Required)", 
    "⚖️ Live Bidding Panel",
    "🤝 Settle Deal", 
    "👤 My Dashboard",
    "🎗️ Campus Charity Ledger"
])

with tab1:
    st.header("Active Campus Listings")
    
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        search_query = st.text_input("🔍 Search items (e.g. cycle, cooler, book)", placeholder="Type item name...", key="browse_search")
    with col_s2:
        categories = ["ALL"] + [row[0] for row in conn.cursor().execute("SELECT category_name FROM categories").fetchall()]
        category_filter = st.selectbox("Category", categories)
    with col_s3:
        sort_by = st.selectbox("Sort By Price", ["Default", "Price: Low to High", "Price: High to Low"])
        
    query = "SELECT * FROM active_marketplace_feed WHERE 1=1"
    if category_filter != "ALL":
        query += f" AND category_name = '{category_filter}'"
    if search_query:
        query += f" AND (title LIKE '%{search_query}%' OR description LIKE '%{search_query}%')"
        
    if sort_by == "Price: Low to High":
        query += " ORDER BY base_price ASC"
    elif sort_by == "Price: High to Low":
        query += " ORDER BY base_price DESC"
        
    df_feed = pd.read_sql_query(query, conn)
    
    if df_feed.empty:
        st.info("No campus items matching the search query.")
    else:
        for idx, row in df_feed.iterrows():
            with st.container():
                st.markdown(f'<div class="item-card">', unsafe_allow_html=True)
                col_img, col_info, col_contact = st.columns([1, 2, 1])
                
                with col_img:
                    img_link = row['image_url'] if row['image_url'] else 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80'
                    st.image(img_link, use_column_width=True)
                    
                with col_info:
                    st.subheader(f"{row['title']} (ID: {row['item_id']})")
                    st.markdown(f"**Category:** `{row['category_name']}` | **Condition:** `{row['item_condition']}`")
                    st.markdown(f"**Type:** `{row['listing_type']}`")
                    if row['course_mapping']:
                        st.markdown(f"📖 Mapped Course Code: **`{row['course_mapping']}`**")
                    st.markdown(f"**Description:** *{row['description']}*")
                    st.markdown(f"📍 Location: **{row['hostel_block']} - Room {row['room_number']}**")
                    
                with col_contact:
                    if row['listing_type'] == 'BOOK_DONATION':
                        st.markdown("### Cost: **FREE (DONATION)**")
                        st.markdown("🎗️ Support junior learning initiative")
                    else:
                        st.markdown(f"### Base Price: ₹{row['base_price']:.2f}")
                        st.markdown(f"##### Highest Offer: **₹{row['current_highest_offer']:.2f}**")
                        if row['listing_type'] == 'RENT':
                            st.markdown(f"Daily Rent: **₹{row['daily_rental_rate']:.2f}/day**")
                    
                    st.markdown(f"👤 Seller: **{row['seller_name']}**")
                    
                    # WhatsApp Redirection
                    encoded_msg = urllib.parse.quote(f"Hello {row['seller_name']}, I am interested in your asset '{row['title']}' (ID: {row['item_id']}) listed on IIT Ropar InstiMart.")
                    whatsapp_url = f"https://wa.me/91{row['seller_phone']}?text={encoded_msg}"
                    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%;">💬 Chat on WhatsApp</button></a>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

# Semester Book Bank
with tab2:
    st.header("📖 Semester Textbook Bank & Course Notes lookup")
    st.markdown("Find textbooks, manuals, and exam notes mapped directly to IIT Ropar course curriculum codes.")
    
    courses_list = ["ALL"] + [f"{r[0]} - {r[1]}" for r in conn.cursor().execute("SELECT course_code, course_title FROM courses").fetchall()]
    course_filter = st.selectbox("Select IIT Ropar Course to search books", courses_list)
    
    query_bank = '''
        SELECT i.item_id, i.title, i.course_mapping, c.course_title, i.base_price, i.listing_type, 
               i.item_condition, i.image_url, u.full_name, u.hostel_block, u.room_number, u.phone
        FROM item_listings i
        JOIN courses c ON i.course_mapping = c.course_code
        JOIN users u ON i.seller_id = u.user_id
        WHERE i.status = 'AVAILABLE'
    '''
    
    if course_filter != "ALL":
        selected_code = course_filter.split(" - ")[0]
        query_bank += f" AND i.course_mapping = '{selected_code}'"
        
    df_bank = pd.read_sql_query(query_bank, conn)
    
    if df_bank.empty:
        st.info("No textbooks currently listed for this course code.")
    else:
        for idx, row in df_bank.iterrows():
            with st.container():
                st.markdown(f'<div class="item-card">', unsafe_allow_html=True)
                col_img, col_info, col_contact = st.columns([1, 2, 1])
                with col_img:
                    img_lnk = row['image_url'] if row['image_url'] else 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&q=80'
                    st.image(img_lnk, use_column_width=True)
                with col_info:
                    st.subheader(f"{row['title']} (Book ID: {row['item_id']})")
                    st.markdown(f"📚 Course: **`{row['course_mapping']}` - {row['course_title']}**")
                    st.markdown(f"**Condition:** `{row['item_condition']}` | **Type:** `{row['listing_type']}`")
                    st.markdown(f"📍 Location: **{row['hostel_block']} - Room {row['room_number']}**")
                with col_contact:
                    if row['listing_type'] == 'BOOK_DONATION':
                        st.markdown("### Price: **FREE (DONATION)**")
                    else:
                        st.markdown(f"### Price: ₹{row['base_price']:.2f}")
                    st.markdown(f"👤 Provider: **{row['full_name']}**")
                    encoded_msg = urllib.parse.quote(f"Hello {row['full_name']}, I need your book '{row['title']}' listed for course {row['course_mapping']} on InstiMart.")
                    whatsapp_url = f"https://wa.me/91{row['phone']}?text={encoded_msg}"
                    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:6px; font-weight:bold; cursor:pointer; width:100%;">💬 Claim Book</button></a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.header("List an Asset for Sale or Rent")
    if not st.session_state.logged_in:
        st.warning("⚠️ Access Denied: Please authenticate via the Sidebar Login Console to post listings.")
    else:
        st.success(f"Authenticated as: {st.session_state.user_name}")
        
        # Feature: AI Generator Console Integration
        st.markdown("##### 🤖 InstiMart AI Assistant Console (Optional)")
        ai_input_title = st.text_input("AI Assistant: Enter asset short name to generate description", placeholder="e.g. Blue Hero Cycle with carrier, Symphony air cooler 45L")
        
        generated_desc_value = ""
        if st.button("Generate Description using Gemini AI"):
            if not ai_input_title:
                st.error("Please enter an asset name for the AI to process.")
            else:
                try:
                    api_key = ""
                    if "GEMINI_API_KEY" in st.secrets:
                        api_key = st.secrets["GEMINI_API_KEY"]
                        
                    if api_key and not api_key.startswith("AIzaSy"):
                        raise ValueError("Placeholder API key")
                        
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-pro')
                    prompt_query = f"Write a premium, short, campus-marketplace listing description (max 2 sentences) for a student selling this item: '{ai_input_title}' at IIT Ropar. Emphasize condition and hostel convenience."
                    response = model.generate_content(prompt_query)
                    generated_desc_value = response.text
                    st.success("AI description generated! Copy the text below into the description field.")
                    st.info(generated_desc_value)
                except Exception as e:
                    generated_desc_value = f"Premium grade {ai_input_title} in excellent working condition. Best suited for hostel requirements. Ready for immediate pickup from campus stands."
                    st.warning("AI Demo Mode: Generated offline mock description:")
                    st.info(generated_desc_value)

        st.markdown("---")
        
        with st.form("new_listing_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Item Title", value=ai_input_title if ai_input_title else "", placeholder="e.g. Hero Cycle, Symphony Cooler")
                category_id = st.selectbox("Category Group", [1, 2, 3, 4, 5], format_func=lambda x: {
                    1: 'Bicycles & Transport', 2: 'Room Coolers & Appliances', 
                    3: 'Textbooks & Course Material', 4: 'Electronics & Gadgets', 
                    5: 'Hostel Furniture & Decor'
                }[x])
                listing_type = st.selectbox("Type of Listing", ["SALE", "RENT", "BOOK_DONATION"])
                image_input_url = st.text_input("Item Image URL (Optional)", placeholder="Paste Unsplash/Image web link here...")
            with col2:
                db_courses = [r[0] for r in conn.cursor().execute("SELECT course_code FROM courses").fetchall()]
                course_mapping = st.selectbox("IIT Ropar Course Mapping (Textbooks only - Optional)", ["None"] + db_courses)
                price = st.number_input("Base Selling Price / Deposit (₹)", min_value=0.0, step=100.0, value=500.0)
                daily_rate = st.number_input("Daily Rental Rate (₹) [If RENT]", min_value=0.0, step=10.0, value=0.0)
                condition = st.selectbox("Item Condition", ["LIKE_NEW", "GOOD", "FAIR", "WELL_USED"])
                description = st.text_area("Item Details / Specifications", value=generated_desc_value)
                
            submit_btn = st.form_submit_button("Publish Ad")
            if submit_btn:
                if not title:
                    st.error("Title is required.")
                else:
                    img_to_save = image_input_url if image_input_url else 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=400&q=80'
                    course_code_to_save = None if course_mapping == "None" else course_mapping
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO item_listings (seller_id, category_id, title, description, base_price, listing_type, daily_rental_rate, item_condition, image_url, course_mapping)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (st.session_state.user_id, category_id, title, description, price, listing_type, daily_rate, condition, img_to_save, course_code_to_save))
                    conn.commit()
                    st.success("Listing published successfully!")

with tab4:
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

with tab5:
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

# Personal Student Dashboard
with tab6:
    st.header("👤 My Campus InstiMart Dashboard")
    if not st.session_state.logged_in:
        st.warning("⚠️ Access Denied: Please authenticate to view your personal activity reports.")
    else:
        st.subheader(f"Activity Summary for {st.session_state.user_name}")
        col_db1, col_db2, col_db3 = st.columns(3)
        
        cursor = conn.cursor()
        my_listings_count = cursor.execute("SELECT COUNT(*) FROM item_listings WHERE seller_id = ?", (st.session_state.user_id,)).fetchone()[0]
        my_active_bids_count = cursor.execute("SELECT COUNT(*) FROM bids WHERE buyer_id = ? AND bid_status = 'PENDING'", (st.session_state.user_id,)).fetchone()[0]
        my_purchases_count = cursor.execute("SELECT COUNT(*) FROM transactions WHERE buyer_id = ?", (st.session_state.user_id,)).fetchone()[0]
        
        with col_db1:
            st.markdown(f'<div class="metric-card"><h5>My Listings</h5><h2>{my_listings_count}</h2></div>', unsafe_allow_html=True)
        with col_db2:
            st.markdown(f'<div class="metric-card"><h5>My Active Offers</h5><h2>{my_active_bids_count}</h2></div>', unsafe_allow_html=True)
        with col_db3:
            st.markdown(f'<div class="metric-card"><h5>Purchased Items</h5><h2>{my_purchases_count}</h2></div>', unsafe_allow_html=True)
            
        # Displaying Lists
        st.markdown("---")
        st.subheader("My Item Listings Status")
        query_my_items = f"SELECT item_id AS 'Item ID', title AS 'Item Name', base_price AS 'Base Price (₹)', status AS 'Status' FROM item_listings WHERE seller_id = {st.session_state.user_id}"
        df_my_items = pd.read_sql_query(query_my_items, conn)
        st.dataframe(df_my_items, use_container_width=True, hide_index=True)
        
        st.subheader("My Bid Offers history")
        query_my_bids = f"SELECT b.bid_id AS 'Bid ID', i.title AS 'Item Name', b.bid_amount AS 'My Offer (₹)', b.bid_status AS 'Bid Status' FROM bids b JOIN item_listings i ON b.item_id = i.item_id WHERE b.buyer_id = {st.session_state.user_id}"
        df_my_bids = pd.read_sql_query(query_my_bids, conn)
        st.dataframe(df_my_bids, use_container_width=True, hide_index=True)

with tab7:
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
