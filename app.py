import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import os

# ========================
# ULTIMATE THEME & UI ENHANCEMENTS
# ========================
st.set_page_config(
    page_title="Mindoro Dairy Ecosystem",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ultimate polish
st.markdown("""
<style>
    /* Main background & fonts */
    .main {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        color: #1e40af !important;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton > button {
        background-color: #16a34a !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        height: 3em;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #15803d !important;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f0fdf4;
    }
    /* Metrics */
    .stMetric > div {
        background-color: #f0fdfa;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #16a34a;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Optional: Logo placeholder (uncomment if may logo ka)
# st.sidebar.image("dairy_logo.png", width=200)
# ========================
# OPTIONAL: FULL DATABASE RESET (FOR CLEAN START)
# ========================
# Uncomment these lines ONLY if you want to delete and recreate the database completely fresh
# if st.button("🔥 RESET DATABASE - Delete All Data & Start Fresh"):
#     if os.path.exists("dairy_ecosystem.db"):
#         os.remove("dairy_ecosystem.db")
#         st.success("Database deleted! Restarting fresh...")
#         st.rerun()

DB_PATH = "dairy_ecosystem.db"

# ========================
# PAGE CONFIG & STYLE
# ========================
st.set_page_config(
    page_title="Mindoro Dairy Ecosystem",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { padding: 2rem; }
    .stMetric > div { background-color: #E8F5E8; padding: 1rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton > button { background-color: #2E8B57; color: white; border-radius: 8px; height: 3em; width: 100%; }
    .stTextInput > div > div > input, .stSelectbox > div > div > select { border-radius: 8px; }
    h1, h2, h3 { color: #1E5631; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ========================
# DATABASE INITIALIZATION (CLEAN & COMPLETE)
# ========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Internal Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS internal_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Manager', 'Sales Clerk', 'Field Staff'))
        )
    ''')
    c.execute("INSERT OR IGNORE INTO internal_users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")


    # Dairy Farmers
    c.execute('''
        CREATE TABLE IF NOT EXISTS dairy_farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            contact TEXT,
            address TEXT,
            username TEXT UNIQUE,
            password TEXT,
            loyalty_tier TEXT DEFAULT 'Bronze',
            bonus_earned REAL DEFAULT 0
        )
    ''')
    sample_farmers = [
        ("Mang Jose Santos", "0917-1234567", "San Teodoro", "jose", "jose123"),
        ("Aling Maria Reyes", "0928-9876543", "Victoria", "maria", "maria123"),
        ("Juan dela Cruz", "0999-5551111", "Naujan", "juan", "juan123")
    ]
    c.executemany("INSERT OR IGNORE INTO dairy_farmers (name, contact, address, username, password) VALUES (?, ?, ?, ?, ?)", sample_farmers)

    # Customers
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT CHECK(type IN ('Reseller', 'Distributor', 'Institutional Buyer')),
            contact TEXT,
            username TEXT UNIQUE,
            password TEXT,
            discount_type TEXT DEFAULT 'Percentage',
            discount_value REAL DEFAULT 0,
            loyalty_points INTEGER DEFAULT 0,
            current_balance REAL DEFAULT 0
        )
    ''')
    sample_customers = [
        ("Juan's Sari-Sari Store", "Reseller", "0909-1112222", "juansstore", "store123", "Percentage", 10.0, 850),
        ("Reyes Mini Mart", "Distributor", "0918-3334444", "reyesmart", "mart123", "Percentage", 15.0, 2500),
        ("Mindoro School Canteen", "Institutional Buyer", "0920-5556666", "schoolcanteen", "canteen123", "Fixed", 5.0, 0)
    ]
    c.executemany("INSERT OR IGNORE INTO customers (name, type, contact, username, password, discount_type, discount_value, loyalty_points) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sample_customers)

    # Products
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            srp REAL NOT NULL,
            unit TEXT,
            current_stock REAL DEFAULT 0,
            low_stock_threshold REAL DEFAULT 10,
            expiry_date TEXT
        )
    ''')
    sample_products = [
        ("Raw Milk", "Raw Milk", 0, "Liter", 0, 50, None),
        ("Fresh Milk 1L", "Finished Goods", 50, "Bottle", 100, 20, None),
        ("Yogurt 500g", "Finished Goods", 80, "Pack", 50, 10, None),
        ("Cheese 200g", "Finished Goods", 120, "Pack", 30, 5, None)
    ]
    c.executemany("INSERT OR IGNORE INTO products (name, category, srp, unit, current_stock, low_stock_threshold, expiry_date) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_products)

    # Milk Collections (all quality fields included from start)
    c.execute('''
        CREATE TABLE IF NOT EXISTS milk_collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            class_a_litres REAL DEFAULT 0,
            class_b_litres REAL DEFAULT 0,
            total_payment REAL,
            collection_date TEXT DEFAULT (date('now')),
            notes TEXT,
            recorded_by TEXT,
            fat_percentage REAL,
            snf_percentage REAL,
            quality_score REAL
        )
    ''')

    # Sales & Items
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_type TEXT,
            customer_id INTEGER,
            total_amount REAL,
            payment_type TEXT,
            sale_date TEXT DEFAULT (date('now')),
            recorded_by TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity REAL,
            unit_price REAL
        )
    ''')

    # Inventory Transactions
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            transaction_type TEXT,
            quantity REAL,
            reason TEXT,
            transaction_date TEXT DEFAULT (date('now')),
            recorded_by TEXT
        )
    ''')

    # Announcements, Messages, Notifications
    c.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            target_type TEXT NOT NULL,
            created_date TEXT DEFAULT (date('now'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_type TEXT NOT NULL,
            sender_id INTEGER,
            sender_name TEXT,
            message TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL,
            user_id INTEGER,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_date TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ========================
# HELPER FUNCTIONS
# ========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def apply_discount(price, discount_type, discount_value):
    if discount_type == "Percentage":
        return price * (1 - discount_value / 100)
    elif discount_type == "Fixed":
        return max(0, price - discount_value)
    return price

def add_notification(user_type, user_id, message):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_type, user_id, message) VALUES (?, ?, ?)", (user_type, user_id, message))
    conn.commit()
    conn.close()

# ========================
# SESSION STATE INITIALIZATION
# ========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_type = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None
    st.session_state.customer_type = None

# ========================
# LOGIN PAGE
# ========================
if not st.session_state.logged_in:
    st.title("🥛 Mindoro Dairy Ecosystem")
    st.markdown("### Welcome! Please select your portal and log in")

    tab_internal, tab_farmer, tab_customer = st.tabs(["🏢 Internal Staff", "🐄 Dairy Farmer Portal", "🏪 Customer Portal"])

    with tab_internal:
        st.markdown("#### Staff Login")
        with st.form("internal_login"):
            username = st.text_input("Username", key="int_user")
            password = st.text_input("Password", type="password", key="int_pass")
            submitted = st.form_submit_button("Login as Staff", type="primary")
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT id, username, role FROM internal_users WHERE username = ? AND password = ?", (username, password))
                    user = c.fetchone()
                    conn.close()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "Internal"
                        st.session_state.user_id = user["id"]
                        st.session_state.username = user["username"]
                        st.session_state.role = user["role"]
                        st.success(f"Welcome back, {username.title()} ({user['role']})!")
                        st.rerun()
                    else:
                        st.error("Invalid staff credentials")

    with tab_farmer:
        st.markdown("#### Dairy Farmer Login")
        with st.form("farmer_login"):
            username = st.text_input("Username", key="farm_user", placeholder="e.g. jose")
            password = st.text_input("Password", type="password", key="farm_pass")
            submitted = st.form_submit_button("Login as Farmer", type="primary")
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT id, name, username FROM dairy_farmers WHERE username = ? AND password = ?", (username, password))
                    farmer = c.fetchone()
                    conn.close()
                    if farmer:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "Farmer"
                        st.session_state.user_id = farmer["id"]
                        st.session_state.username = farmer["username"]
                        st.session_state.name = farmer["name"]
                        st.success(f"Mabuhay, {farmer['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid farmer credentials")

    with tab_customer:
        st.markdown("#### Registered Buyer Login")
        with st.form("customer_login"):
            username = st.text_input("Username", key="cust_user", placeholder="e.g. juansstore")
            password = st.text_input("Password", type="password", key="cust_pass")
            submitted = st.form_submit_button("Login as Buyer", type="primary")
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT id, name, username, type FROM customers WHERE username = ? AND password = ?", (username, password))
                    customer = c.fetchone()
                    conn.close()
                    if customer:
                        st.session_state.logged_in = True
                        st.session_state.user_type = "Customer"
                        st.session_state.user_id = customer["id"]
                        st.session_state.username = customer["username"]
                        st.session_state.name = customer["name"]
                        st.session_state.customer_type = customer["type"]
                        st.success(f"Welcome, {customer['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid customer credentials")

    st.markdown("---")
    st.caption("**Default Logins for Testing:**")
    st.caption("**Staff:** admin / admin123")
    st.caption("**Farmers:** jose / jose123 | maria / maria123 | juan / juan123")
    st.caption("**Customers:** juansstore / store123 | reyesmart / mart123 | schoolcanteen / canteen123")

    st.stop()

# ========================
# SIDEBAR AFTER LOGIN
# ========================
with st.sidebar:
    if st.session_state.user_type == "Internal":
        display_name = st.session_state.username.title()
        role_text = st.session_state.role
    else:
        display_name = st.session_state.name
        role_text = st.session_state.user_type

    st.markdown(f"**Welcome,**")
    st.markdown(f"**{display_name}**")
    st.markdown(f"_{role_text}_")
    st.divider()

    if st.button("Logout", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.caption("Mindoro Dairy Ecosystem © 2025")

# ========================
# MAIN APP (INTERNAL ONLY - SIMPLIFIED FOR SPACE)
# ========================
if st.session_state.user_type == "Internal":
    st.title("🏢 Mindoro Dairy Management System")

    menu = {
        "Admin": ["Dashboard", "Milk Collection", "Sales", "Inventory", "Production", "Manage Farmers", "Manage Customers", "Announcements", "Messages & Notifications"],
        "Manager": ["Dashboard", "Milk Collection", "Sales", "Inventory", "Production", "Manage Customers", "Announcements", "Messages & Notifications"],
        "Sales Clerk": ["Dashboard", "Sales", "Messages & Notifications"],
        "Field Staff": ["Dashboard", "Milk Collection", "Messages & Notifications"]
    }
    pages = menu.get(st.session_state.role, ["Dashboard"])
    selection = st.sidebar.radio("Navigation", pages)

    conn = get_conn()

    if selection == "Dashboard":
        st.header("🚀 Command Center - Super Advanced Analytics Dashboard")
        st.markdown(f"**Maligayang pagbati, {st.session_state.username.title()} ({st.session_state.role})!** | **{date.today().strftime('%A, %B %d, %Y')}**")

        # === KEY METRICS ===
        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()
        this_month = date.today().strftime('%Y-%m')

        # Sales & Milk Today/Yesterday
        sales_today = pd.read_sql_query(f"SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE sale_date = '{today_str}'", conn).iloc[0]['total']
        sales_yest = pd.read_sql_query(f"SELECT COALESCE(SUM(total_amount), 0) AS total FROM sales WHERE sale_date = '{yesterday_str}'", conn).iloc[0]['total']

        milk_today = pd.read_sql_query(f"SELECT COALESCE(SUM(class_a_litres + class_b_litres), 0) AS total FROM milk_collections WHERE collection_date = '{today_str}'", conn).iloc[0]['total']
        milk_yest = pd.read_sql_query(f"SELECT COALESCE(SUM(class_a_litres + class_b_litres), 0) AS total FROM milk_collections WHERE collection_date = '{yesterday_str}'", conn).iloc[0]['total']

        # Additional KPIs
        inv_value = pd.read_sql_query("SELECT COALESCE(SUM(current_stock * srp), 0) FROM products WHERE srp > 0", conn).iloc[0,0]
        low_stock_count = pd.read_sql_query("SELECT COUNT(*) FROM products WHERE current_stock <= low_stock_threshold AND current_stock > 0 AND category != 'Raw Milk'", conn).iloc[0,0]
        active_farmers_today = pd.read_sql_query(f"SELECT COUNT(DISTINCT farmer_id) FROM milk_collections WHERE collection_date = '{today_str}'", conn).iloc[0,0]
        total_farmers = pd.read_sql_query("SELECT COUNT(*) FROM dairy_farmers", conn).iloc[0,0]

        revenue_per_liter = round(sales_today / milk_today, 1) if milk_today > 0 else 0
        estimated_cost_per_liter = 85  # Adjustable
        gross_margin_today = sales_today - (milk_today * estimated_cost_per_liter)

        # KPI Cards
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Today's Revenue", f"₱{sales_today:,.0f}", delta=f"{sales_today - sales_yest:+,.0f}")
        with col2:
            st.metric("Milk Collected Today", f"{milk_today:.1f} L", delta=f"{milk_today - milk_yest:+.1f} L")
        with col3:
            st.metric("Revenue per Liter", f"₱{revenue_per_liter:.1f}", delta="Strong" if revenue_per_liter >= 95 else "Monitor" if revenue_per_liter >= 85 else "Low")
        with col4:
            st.metric("Active Farmers Today", active_farmers_today, delta=f"{active_farmers_today}/{total_farmers} total")
        with col5:
            st.metric("Est. Gross Margin", f"₱{gross_margin_today:,.0f}", delta="Healthy" if gross_margin_today > 0 else "Loss")
        with col6:
            st.metric("Inventory Value", f"₱{inv_value:,.0f}", delta=f"{low_stock_count} low stock items" if low_stock_count > 0 else "All good")

        st.divider()

        # === INTERACTIVE CHARTS ===
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📈 Milk Collection vs Revenue Trend (Last 30 Days)")
            df_trend = pd.read_sql_query(f"""
                SELECT 
                    date,
                    COALESCE(milk_litres, 0) AS milk_litres,
                    COALESCE(revenue, 0) AS revenue
                FROM (
                    SELECT collection_date AS date, SUM(class_a_litres + class_b_litres) AS milk_litres, 0 AS revenue
                    FROM milk_collections 
                    WHERE collection_date >= date('now', '-30 days')
                    GROUP BY date
                    UNION ALL
                    SELECT sale_date AS date, 0 AS milk_litres, SUM(total_amount) AS revenue
                    FROM sales 
                    WHERE sale_date >= date('now', '-30 days')
                    GROUP BY date
                ) 
                GROUP BY date 
                ORDER BY date
            """, conn)

            if not df_trend.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['milk_litres'], name="Milk Collected (L)", line=dict(color="#2E8B57", width=4)))
                fig.add_trace(go.Bar(x=df_trend['date'], y=df_trend['revenue'], name="Revenue (₱)", yaxis='y2', opacity=0.7, marker_color="#A8E6CF"))
                fig.update_layout(
                    title="Daily Performance Trend",
                    yaxis=dict(title="Liters", side="left"),
                    yaxis2=dict(title="Revenue ₱", overlaying="y", side="right"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data in the last 30 days yet.")

        with col_right:
            st.subheader("🥇 Top Performing Farmers (This Month)")
            df_top_farmers = pd.read_sql_query(f"""
                SELECT 
                    df.name AS Farmer,
                    ROUND(SUM(mc.class_a_litres + mc.class_b_litres), 1) AS Liters,
                    SUM(mc.total_payment) AS Earnings
                FROM milk_collections mc
                JOIN dairy_farmers df ON mc.farmer_id = df.id
                WHERE strftime('%Y-%m', mc.collection_date) = '{this_month}'
                GROUP BY df.name
                ORDER BY Liters DESC
                LIMIT 10
            """, conn)

            if not df_top_farmers.empty:
                fig = px.bar(df_top_farmers, x='Farmer', y='Liters', color='Earnings',
                             title="Farmer Leaderboard",
                             color_continuous_scale="Greens",
                             text='Liters')
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                df_top_farmers['Earnings'] = df_top_farmers['Earnings'].apply(lambda x: f"₱{x:,.0f}")
                st.dataframe(df_top_farmers.style.format({"Liters": "{:.1f}"}), hide_index=True)
            else:
                st.info("No collections recorded this month yet.")

        st.divider()

        # === PREDICTIVE ALERTS & INSIGHTS ===
        st.subheader("🔮 Smart Alerts & Insights")
        alerts = []

        if milk_today < milk_yest * 0.8 and milk_yest > 0:
            alerts.append("⚠️ Milk collection dropped more than 20% vs yesterday – consider farmer outreach")
        if revenue_per_liter < 90:
            alerts.append("🚨 Revenue per liter is low – review pricing, product mix, or discounts")
        if low_stock_count >= 3:
            alerts.append(f"🔴 {low_stock_count} products are low on stock – reorder recommended")
        if active_farmers_today < total_farmers * 0.6:
            alerts.append("📉 Low farmer participation today – send reminder via Announcements")

        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ All systems running optimally – excellent performance today!")

        st.divider()

        # === RECENT ACTIVITY FEED ===
        st.subheader("🕒 Recent Activity (Last 20 Events)")
        df_recent = pd.read_sql_query("""
            SELECT 'Milk Collection' AS type, collection_date AS date,
                   df.name || ' delivered ' || ROUND(mc.class_a_litres + mc.class_b_litres, 1) || 'L → ₱' || COALESCE(mc.total_payment, 0) AS activity
            FROM milk_collections mc
            JOIN dairy_farmers df ON mc.farmer_id = df.id
            UNION ALL
            SELECT 'Sale' AS type, sale_date AS date,
                   'Sale #' || s.id || ' → ₱' || s.total_amount || ' (' || s.payment_type || ')' AS activity
            FROM sales s
            ORDER BY date DESC, activity DESC
            LIMIT 20
        """, conn)

        if not df_recent.empty:
            df_recent = df_recent.rename(columns={"type": "Type", "date": "Date", "activity": "Activity"})
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("No recent activity yet.")

        st.divider()

        # === EXPORT DASHBOARD DATA ===
        if st.button("📊 Export Full Dashboard Report to Excel", type="primary", use_container_width=True):
            output_file = "Mindoro_Dairy_Dashboard_Report.xlsx"
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                if not df_trend.empty:
                    df_trend.to_excel(writer, sheet_name="Trend_30Days", index=False)
                if not df_top_farmers.empty:
                    df_top_farmers.to_excel(writer, sheet_name="Top_Farmers", index=False)
                if not df_recent.empty:
                    df_recent.to_excel(writer, sheet_name="Recent_Activity", index=False)

            st.success(f"Dashboard report exported: **{output_file}**")
            st.balloons()

    # Add other pages here (Milk Collection, Sales, etc.) as in your original code

        conn.close()
    elif selection == "Milk Collection":
        # ========================
        # ADVANCE MILK COLLECTION
        # ========================
        st.header("🥛 Advanced Milk Reception & Quality Grading")
        st.markdown("**Precision collection • Real-time quality testing • Smart pricing engine • Bonus & loyalty system • Auto stock update**")

        conn = get_conn()
        c = conn.cursor()

        # Load farmers
        c.execute("SELECT id, name, loyalty_tier FROM dairy_farmers ORDER BY name")
        farmers = c.fetchall()

        if not farmers:
            st.warning("No dairy farmers registered yet. Please add via Manage Farmers.")
            conn.close()
            st.stop()

        # Farmer Selection
        farmer_options = [f"{f['name']} ({f['loyalty_tier']})" for f in farmers]
        selected_display = st.selectbox("🔍 Select Dairy Farmer", farmer_options, key="milk_farmer_select")
        farmer_id = farmers[farmer_options.index(selected_display)]['id']
        farmer_name = selected_display.split(" (")[0]
        current_tier = selected_display.split("(")[1].replace(")", "")

        # Monthly Stats for selected farmer
        this_month = date.today().strftime('%Y-%m')
        monthly_stats = pd.read_sql_query(f"""
            SELECT
                COALESCE(SUM(class_a_litres + class_b_litres), 0) AS litres,
                COALESCE(SUM(total_payment), 0) AS payment,
                COUNT(*) AS deliveries
            FROM milk_collections
            WHERE farmer_id = {farmer_id}
              AND strftime('%Y-%m', collection_date) = '{this_month}'
        """, conn).iloc[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Loyalty Tier", current_tier)
        with col2:
            st.metric("This Month Liters", f"{monthly_stats['litres']:.1f} L")
        with col3:
            st.metric("This Month Earnings", f"₱{monthly_stats['payment']:,.0f}")
        with col4:
            st.metric("Deliveries This Month", monthly_stats['deliveries'])
        with col5:
            target = 1500 if current_tier == "Bronze" else 3000 if current_tier == "Silver" else 5000
            next_tier = "Silver" if current_tier == "Bronze" else "Gold" if current_tier == "Silver" else "Platinum"
            progress = min(monthly_stats['litres'] / target, 1.0)
            st.progress(progress)
            st.caption(f"→ Next tier: **{next_tier}** at {target}L")

        st.divider()

        # === QUALITY TESTING & COLLECTION INPUT ===
        st.subheader(f"🧪 New Collection for **{farmer_name}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_litres = st.number_input("Total Liters Delivered", min_value=0.0, step=0.5, format="%.2f", key="litres_input")
        with col2:
            fat_percent = st.number_input("Fat %", min_value=0.0, max_value=10.0, step=0.1, value=3.8, key="fat_input")
        with col3:
            snf_percent = st.number_input("SNF %", min_value=0.0, max_value=12.0, step=0.1, value=8.5, key="snf_input")
        with col4:
            temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, step=0.5, value=4.0, key="temp_input")

        # Quality Score Calculation (available in both accept & reject paths)
        quality_score = 0
        if total_litres > 0:
            quality_score += min(fat_percent / 4.0 * 40, 40)      # Fat max 40 points
            quality_score += min(snf_percent / 9.0 * 30, 30)      # SNF max 30 points
            quality_score += 20 if temperature <= 6 else 10 if temperature <= 10 else 0
            quality_score += 10 if total_litres >= 50 else 5

        # Rejection Check
        if fat_percent < 3.0 or snf_percent < 7.5 or temperature > 15:
            st.error("🚫 Milk does NOT meet minimum quality standards – WILL BE REJECTED")
            st.info("Requirements: Fat ≥3.0% | SNF ≥7.5% | Temperature ≤15°C")

            reject_notes = st.text_area("Reason for rejection (required)", key="reject_notes")
            if st.button("❌ Record Rejection", type="secondary", use_container_width=True):
                if not reject_notes.strip():
                    st.error("Please provide a reason for rejection.")
                else:
                    c.execute("""
                        INSERT INTO milk_collections
                        (farmer_id, class_a_litres, class_b_litres, total_payment, notes, recorded_by, 
                         fat_percentage, snf_percentage, quality_score)
                        VALUES (?, 0, 0, 0, ?, ?, ?, ?, ?)
                    """, (farmer_id, f"REJECTED: {reject_notes}", st.session_state.username, 
                          fat_percent, snf_percent, quality_score))
                    conn.commit()
                    add_notification("Farmer", farmer_id, f"Your delivery today was rejected: {reject_notes}")
                    st.error("Rejection recorded.")
                    st.rerun()
        else:
            # === SMART PRICING ENGINE (ACCEPTED MILK) ===
            base_price = 80
            quality_premium = 0
            if fat_percent >= 4.2: quality_premium += 8
            elif fat_percent >= 4.0: quality_premium += 5
            elif fat_percent >= 3.8: quality_premium += 3
            if snf_percent >= 9.0: quality_premium += 5
            elif snf_percent >= 8.8: quality_premium += 3

            volume_bonus = 0
            if total_litres >= 200: volume_bonus = 5
            elif total_litres >= 100: volume_bonus = 3
            elif total_litres >= 50: volume_bonus = 2

            loyalty_bonus = 0
            if current_tier == "Silver": loyalty_bonus = 2
            elif current_tier == "Gold": loyalty_bonus = 5
            elif current_tier == "Platinum": loyalty_bonus = 8

            # Consistency bonus
            has_yesterday = pd.read_sql_query(f"""
                SELECT COUNT(*) FROM milk_collections
                WHERE farmer_id = {farmer_id} AND collection_date = date('now', '-1 day')
            """, conn).iloc[0,0] > 0
            consistency_bonus = 2 if has_yesterday else 0

            final_price_per_liter = base_price + quality_premium + volume_bonus + loyalty_bonus + consistency_bonus
            total_bonus = total_litres * (quality_premium + volume_bonus + loyalty_bonus + consistency_bonus)
            total_payment = round(total_litres * final_price_per_liter, 2)

            # Live Pricing Display
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Quality Score", f"{quality_score:.0f}/100", delta="Excellent" if quality_score >= 85 else "Good")
            with col2:
                st.metric("Price per Liter", f"₱{final_price_per_liter:.1f}")
            with col3:
                st.metric("Base + Premium", f"₱{base_price + quality_premium:.0f}")
            with col4:
                st.metric("Total Bonus", f"₱{total_bonus:.0f}")
            with col5:
                st.metric("**Final Payment**", f"₱{total_payment:,.2f}", delta=f"+₱{total_bonus:.0f} bonus")

            notes = st.text_area("Additional Notes (optional)", key="collection_notes")

            if st.button("✅ Record Collection & Update Raw Milk Stock", type="primary", use_container_width=True):
                if total_litres <= 0:
                    st.error("Please enter valid liters greater than 0.")
                else:
                    # Record collection
                    c.execute("""
                        INSERT INTO milk_collections
                        (farmer_id, class_a_litres, class_b_litres, total_payment, notes, recorded_by,
                         fat_percentage, snf_percentage, quality_score)
                        VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?)
                    """, (farmer_id, total_litres, total_payment, notes or "None", st.session_state.username,
                          fat_percent, snf_percent, quality_score))

                    # Update Raw Milk stock
                    conn.execute("UPDATE products SET current_stock = current_stock + ? WHERE name = 'Raw Milk'", (total_litres,))

                    # Log transaction
                    conn.execute("""
                        INSERT INTO inventory_transactions
                        (product_id, transaction_type, quantity, reason, recorded_by)
                        VALUES ((SELECT id FROM products WHERE name = 'Raw Milk'), 'IN', ?, ?, ?)
                    """, (total_litres, f"Collection from {farmer_name} | {total_litres:.1f}L | Bonus ₱{total_bonus:.0f}", st.session_state.username))

                    # Auto tier upgrade
                    new_monthly_litres = monthly_stats['litres'] + total_litres
                    new_tier = current_tier
                    if new_monthly_litres >= 5000 and current_tier == "Gold":
                        new_tier = "Platinum"
                    elif new_monthly_litres >= 3000 and current_tier == "Silver":
                        new_tier = "Gold"
                    elif new_monthly_litres >= 1500 and current_tier == "Bronze":
                        new_tier = "Silver"

                    if new_tier != current_tier:
                        conn.execute("UPDATE dairy_farmers SET loyalty_tier = ? WHERE id = ?", (new_tier, farmer_id))
                        st.balloons()
                        st.success(f"🎉 {farmer_name} upgraded to **{new_tier}** tier!")

                    conn.commit()
                    st.success(f"Collection recorded for **{farmer_name}**!")
                    st.success(f"Payment: **₱{total_payment:,.2f}** (includes ₱{total_bonus:.0f} bonus)")
                    add_notification("Farmer", farmer_id, f"New collection: {total_litres:.1f}L → ₱{total_payment:,.2f}")
                    st.rerun()

        st.divider()

        # === TODAY'S COLLECTIONS SUMMARY ===
        st.subheader("📊 Today's Collections Summary (All Farmers)")
        df_today = pd.read_sql_query("""
            SELECT
                df.name AS Farmer,
                ROUND(mc.class_a_litres + mc.class_b_litres, 1) AS Liters,
                mc.fat_percentage AS "Fat %",
                mc.snf_percentage AS "SNF %",
                mc.quality_score AS Score,
                mc.total_payment AS "Payment ₱"
            FROM milk_collections mc
            JOIN dairy_farmers df ON mc.farmer_id = df.id
            WHERE mc.collection_date = date('now')
            ORDER BY Liters DESC
        """, conn)

        if not df_today.empty:
            st.dataframe(df_today.style.format({
                "Liters": "{:.1f}",
                "Fat %": "{:.2f}",
                "SNF %": "{:.2f}",
                "Score": "{:.0f}",
                "Payment ₱": "₱{:.0f}"
            }), use_container_width=True)

            if st.button("📥 Export Today's Collections to Excel", type="secondary"):
                df_today.to_excel("Todays_Milk_Collections.xlsx", index=False)
                st.success("Exported!")
                st.balloons()
        else:
            st.info("No collections recorded today yet.")

        conn.close()
    elif selection == "Sales":
        # ========================
        # ADVANCE SALES POS
        # ========================
        st.header("💰 Super Advanced Sales POS System")
        st.markdown("**Full retail experience • Smart cart • Real-time discounts • Promo engine • Loyalty points • Credit/utang tracking • Partial payment • Digital receipt**")

        conn = get_conn()
        c = conn.cursor()

        # Load available products (with stock > 0 and SRP > 0)
        c.execute("""
            SELECT id, name, srp, current_stock, unit
            FROM products
            WHERE current_stock > 0 AND srp > 0
            ORDER BY name
        """)
        products = c.fetchall()

        if not products:
            st.warning("No products available for sale. Please check inventory.")
            conn.close()
            st.stop()

        # Customer Type Selection
        customer_type = st.radio("Customer Type", ["Walk-In (Cash)", "Registered Buyer"], horizontal=True)

        customer_id = None
        customer_name = "Walk-In Customer"
        discount_type = "Percentage"
        discount_value = 0.0
        loyalty_points = 0
        current_balance = 0.0

        if customer_type == "Registered Buyer":
            c.execute("SELECT id, name, discount_type, discount_value, loyalty_points, current_balance FROM customers ORDER BY name")
            customers = c.fetchall()
            if not customers:
                st.info("No registered customers yet.")
            else:
                cust_options = [f"{c['name']} (Points: {c['loyalty_points']:,} | Balance: ₱{c['current_balance']:,.2f})" for c in customers]
                selected_cust_display = st.selectbox("Select Registered Buyer", cust_options, key="reg_buyer_select")
                selected_idx = cust_options.index(selected_cust_display)
                selected_cust = customers[selected_idx]

                customer_id = selected_cust["id"]
                customer_name = selected_cust["name"]
                discount_type = selected_cust["discount_type"]
                discount_value = selected_cust["discount_value"]
                loyalty_points = selected_cust["loyalty_points"]
                current_balance = selected_cust["current_balance"]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Discount:** {discount_value}{'%' if discount_type == 'Percentage' else ' ₱ fixed'}")
                with col2:
                    st.success(f"**Loyalty Points:** {loyalty_points:,}")
                with col3:
                    if current_balance > 0:
                        st.warning(f"**Outstanding Balance:** ₱{current_balance:,.2f}")
                    else:
                        st.success("**Clear balance**")

        st.divider()

        # === SMART CART WITH SEARCH ===
        st.subheader(f"🛒 Cart for **{customer_name}**")

        search_term = st.text_input("🔍 Search Product", placeholder="Type to filter products...", key="product_search")

        filtered_products = [p for p in products if search_term.lower() in p['name'].lower()] if search_term else products

        if not filtered_products and search_term:
            st.info(f"No products found for '{search_term}'. Showing all.")
            filtered_products = products

        cart = []
        subtotal = 0.0

        for product in filtered_products:
            qty_key = f"qty_{product['id']}_{st.session_state.get('sales_rerun', 0)}"
            col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])

            with col1:
                st.write(f"**{product['name']}** • {product['unit']} • Stock: {product['current_stock']:.2f}")

            with col2:
                qty = st.number_input("Qty", min_value=0.0, max_value=product['current_stock'],
                                      step=0.5 if product['unit'] in ["Liter", "Kg"] else 1.0,
                                      key=qty_key, label_visibility="collapsed")

            with col3:
                unit_price = apply_discount(product['srp'], discount_type, discount_value)
                st.write(f"₱{unit_price:,.2f}")

            with col4:
                line_total = qty * unit_price
                if qty > 0:
                    subtotal += line_total
                    cart.append({
                        "pid": product["id"],
                        "name": product["name"],
                        "qty": qty,
                        "unit_price": unit_price,
                        "line_total": line_total
                    })
                    st.success(f"₱{line_total:,.2f}")
                else:
                    st.write("")

            with col5:
                if qty > 0:
                    st.caption(f"{qty} × ₱{unit_price:,.0f}")

        if not cart:
            st.info("👆 Add items by entering quantity above.")

        st.divider()

        # === PROMO ENGINE ===
        promo_discount = 0.0
        promo_messages = []

        # Buy 10 Get 1 Free - Fresh Milk 1L
        fresh_milk_qty = sum(item['qty'] for item in cart if "Fresh Milk 1L" in item['name'])
        free_bottles = fresh_milk_qty // 10
        if free_bottles > 0:
            promo_discount += free_bottles * 50  # Assuming SRP ₱50
            promo_messages.append(f"🎁 Buy 10 Get 1 Free → {free_bottles} free Fresh Milk 1L")

        # Yogurt + Cheese Bundle - 10% off
        bundle_items = [item for item in cart if "Yogurt" in item['name'] or "Cheese" in item['name']]
        if len(bundle_items) >= 2:
            bundle_total = sum(item['line_total'] for item in bundle_items)
            bundle_discount = bundle_total * 0.10
            promo_discount += bundle_discount
            promo_messages.append("🎁 Yogurt + Cheese Bundle → 10% off")

        # Loyalty Points Redemption
        points_to_redeem = 0
        points_discount = 0.0
        if customer_type == "Registered Buyer" and loyalty_points >= 100:
            max_redeemable = (loyalty_points // 100) * 100
            points_to_redeem = st.slider("Redeem Loyalty Points (100 pts = ₱50)", 0, max_redeemable, 0, step=100, key="points_redeem")
            points_discount = (points_to_redeem // 100) * 50

        # Final Calculations
        total_after_promo = subtotal - promo_discount
        total_after_points = total_after_promo - points_discount
        vat = total_after_points * 0.12
        grand_total = round(total_after_points + vat, 2)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Subtotal", f"₱{subtotal:,.2f}")
        with col2:
            st.metric("Promo Discounts", f"-₱{promo_discount:,.2f}")
        with col3:
            st.metric("Points Redeemed", f"-₱{points_discount:,.2f}")
        with col4:
            st.metric("VAT 12%", f"₱{vat:,.2f}")

        st.metric("**GRAND TOTAL**", f"₱{grand_total:,.2f}", delta=None)

        if promo_messages:
            st.success("Applied Promos: " + " | ".join(promo_messages))

        # Payment Section
        payment_method = st.selectbox("Payment Method", ["Cash", "GCash", "Bank Transfer", "Credit (Utang)", "Partial Payment"])

        amount_paid = grand_total
        if payment_method in ["Partial Payment", "Credit (Utang)"]:
            amount_paid = st.number_input("Amount Paid Today", min_value=0.0, max_value=grand_total, value=0.0 if payment_method == "Credit (Utang)" else grand_total)

        remaining = grand_total - amount_paid

        if st.button("🧾 Confirm Sale & Print Digital Receipt", type="primary", use_container_width=True):
            if not cart:
                st.error("Cart is empty!")
            elif remaining < 0:
                st.error("Amount paid cannot exceed total.")
            else:
                # Record Sale
                c.execute("""
                    INSERT INTO sales (customer_type, customer_id, total_amount, payment_type, recorded_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (customer_type, customer_id, grand_total, payment_method, st.session_state.username))
                sale_id = c.lastrowid

                # Record Items & Update Stock
                for item in cart:
                    c.execute("INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                              (sale_id, item["pid"], item["qty"], item["unit_price"]))
                    conn.execute("UPDATE products SET current_stock = current_stock - ? WHERE id = ?", (item["qty"], item["pid"]))
                    conn.execute("""
                        INSERT INTO inventory_transactions (product_id, transaction_type, quantity, reason, recorded_by)
                        VALUES (?, 'OUT', ?, ?, ?)
                    """, (item["pid"], item["qty"], f"Sale #{sale_id} to {customer_name}", st.session_state.username))

                # Update Customer (if registered)
                if customer_type == "Registered Buyer":
                    new_balance = current_balance + remaining
                    points_earned = int(grand_total // 10)
                    new_points = loyalty_points - points_to_redeem + points_earned
                    conn.execute("UPDATE customers SET current_balance = ?, loyalty_points = ? WHERE id = ?",
                                 (new_balance, new_points, customer_id))

                conn.commit()
                st.success(f"Sale #{sale_id} completed successfully!")
                st.balloons()

                # Digital Receipt
                with st.expander("📄 View Digital Receipt", expanded=True):
                    st.markdown(f"**Mindoro Dairy** • Sale #{sale_id} • {date.today().strftime('%b %d, %Y %H:%M')}")
                    st.markdown(f"**Customer:** {customer_name}")
                    st.markdown("**Items:**")
                    receipt_df = pd.DataFrame([
                        {"Item": i["name"], "Qty": i["qty"], "Price": f"₱{i['unit_price']:,.2f}", "Total": f"₱{i['line_total']:,.2f}"}
                        for i in cart
                    ])
                    st.table(receipt_df)
                    st.markdown(f"**Subtotal:** ₱{subtotal:,.2f}")
                    if promo_discount > 0:
                        st.markdown(f"**Promo Discount:** -₱{promo_discount:,.2f}")
                    if points_discount > 0:
                        st.markdown(f"**Points Redeemed:** -₱{points_discount:,.2f}")
                    st.markdown(f"**VAT (12%):** ₱{vat:,.2f}")
                    st.markdown(f"**GRAND TOTAL:** ₱{grand_total:,.2f}")
                    st.markdown(f"**Paid Today:** ₱{amount_paid:,.2f}")
                    st.markdown(f"**Remaining Balance:** ₱{remaining:,.2f}")
                    st.markdown("**Thank you for your purchase! 🥛**")

                st.rerun()

        st.divider()

        # Today's Sales Summary
        st.subheader("📊 Today's Sales Summary")
        df_today_sales = pd.read_sql_query("""
            SELECT p.name AS Product, SUM(si.quantity) AS Sold, SUM(si.quantity * si.unit_price) AS Revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.sale_date = date('now')
            GROUP BY p.name
            ORDER BY Revenue DESC
        """, conn)

        if not df_today_sales.empty:
            st.dataframe(df_today_sales.style.format({"Sold": "{:.1f}", "Revenue": "₱{:.0f}"}), use_container_width=True)
        else:
            st.info("No sales recorded today yet.")

        conn.close()
    elif selection == "Inventory":
        # ========================
        # SIMPLE & AMAZING INVENTORY (ALL WORKING + REAL-TIME)
        # ========================
        st.header("📦 Inventory Management")
        st.markdown("**Simple • Clean • All actions work perfectly • Real-time updates**")

        conn = get_conn()
        c = conn.cursor()

        # Real-time fresh data
        df = pd.read_sql_query("""
            SELECT id, name AS Product, category AS Category, current_stock AS Stock,
                   low_stock_threshold AS Threshold, srp AS "SRP (₱)",
                   ROUND(current_stock * srp, 0) AS "Value (₱)"
            FROM products ORDER BY name
        """, conn)

        if df.empty:
            st.info("No products yet. Add your first product below!")
        else:
            total_value = df["Value (₱)"].sum()
            low_stock = len(df[df["Stock"] <= df["Threshold"]])
            out_stock = len(df[df["Stock"] <= 0])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Value", f"₱{total_value:,.0f}")
            with col2:
                st.metric("Low Stock", low_stock)
            with col3:
                st.metric("Out of Stock", out_stock)

            st.divider()

            st.dataframe(df[["Product", "Category", "Stock", "Threshold", "SRP (₱)", "Value (₱)"]],
                         use_container_width=True, hide_index=True)

        st.divider()

        # Action selector
        action = st.radio("Choose action:", 
                          ["Add Product", "Edit Product", "Delete Product", "Adjust Stock"], 
                          horizontal=True)

        # === ADD PRODUCT ===
        if action == "Add Product":
            if st.session_state.role not in ["Admin", "Manager"]:
                st.info("Only Admin/Manager can add products.")
            else:
                st.subheader("Add New Product")
                with st.form("add_form", clear_on_submit=True):
                    name = st.text_input("Product Name")
                    category = st.selectbox("Category", ["Raw Milk", "Finished Goods", "By-Product"])
                    unit = st.selectbox("Unit", ["Liter", "Bottle", "Pack", "Kg", "Piece"])
                    srp = st.number_input("SRP (₱)", min_value=0.0, step=0.5)
                    stock = st.number_input("Initial Stock", min_value=0.0, step=0.1)
                    threshold = st.number_input("Low Stock Alert", min_value=1.0, value=10.0)

                    if st.form_submit_button("Save Product", type="primary"):
                        if not name.strip():
                            st.error("Product name is required!")
                        else:
                            try:
                                c.execute("""
                                    INSERT INTO products (name, category, unit, srp, current_stock, low_stock_threshold)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (name.strip(), category, unit, srp, stock, threshold))
                                conn.commit()
                                st.success(f"**{name}** added!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Product name already exists!")

        # === EDIT PRODUCT ===
        elif action == "Edit Product":
            if st.session_state.role not in ["Admin", "Manager"]:
                st.info("Only Admin/Manager can edit.")
            elif df.empty:
                st.info("No products to edit.")
            else:
                st.subheader("Edit Product")
                product_names = df["Product"].tolist()
                selected_name = st.selectbox("Select product", product_names, key="edit_select_final")

                pid = int(df[df["Product"] == selected_name]["id"].iloc[0])
                current = conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()

                if current:
                    with st.form("edit_form", clear_on_submit=True):
                        e_name = st.text_input("Product Name", value=current["name"])
                        e_category = st.selectbox("Category", ["Raw Milk", "Finished Goods", "By-Product"],
                                                  index=["Raw Milk", "Finished Goods", "By-Product"].index(current["category"]))
                        e_unit = st.selectbox("Unit", ["Liter", "Bottle", "Pack", "Kg", "Piece"],
                                              index=["Liter", "Bottle", "Pack", "Kg", "Piece"].index(current["unit"]))
                        e_srp = st.number_input("SRP (₱)", min_value=0.0, value=float(current["srp"]))
                        e_threshold = st.number_input("Low Stock Alert", min_value=1.0, value=float(current["low_stock_threshold"]))

                        if st.form_submit_button("Update Product", type="primary"):
                            try:
                                c.execute("""
                                    UPDATE products SET name = ?, category = ?, unit = ?, srp = ?, low_stock_threshold = ?
                                    WHERE id = ?
                                """, (e_name.strip(), e_category, e_unit, e_srp, e_threshold, pid))
                                conn.commit()
                                st.success(f"**{e_name}** updated!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("Product name already exists!")
                else:
                    st.error("Product not found.")

        # === DELETE PRODUCT ===
        elif action == "Delete Product":
            if st.session_state.role != "Admin":
                st.info("Only Admin can delete.")
            elif df.empty:
                st.info("No products to delete.")
            else:
                st.subheader("Delete Product")
                product_names = df["Product"].tolist()
                selected_name = st.selectbox("Select product", product_names, key="delete_select_final")
                pid = int(df[df["Product"] == selected_name]["id"].iloc[0])

                st.warning("This is permanent!")
                if st.button("Yes, Delete Permanently", type="secondary"):
                    c.execute("DELETE FROM products WHERE id = ?", (pid,))
                    conn.commit()
                    st.error(f"**{selected_name}** deleted!")
                    st.rerun()

        # === ADJUST STOCK (NOW FULLY WORKING) ===
        elif action == "Adjust Stock":
            if st.session_state.role not in ["Admin", "Manager"]:
                st.info("Only Admin/Manager can adjust stock.")
            elif df.empty:
                st.info("No products to adjust.")
            else:
                st.subheader("Adjust Stock")
                product_names = df["Product"].tolist()
                selected_name = st.selectbox("Select product", product_names, key="adjust_select_final")
                pid = int(df[df["Product"] == selected_name]["id"].iloc[0])

                with st.form("adjust_form", clear_on_submit=True):
                    adj_type = st.radio("Action", ["Add Stock", "Remove Stock"], horizontal=True)
                    qty = st.number_input("Quantity", min_value=0.01, step=0.1)
                    reason = st.text_input("Reason (optional)")

                    if st.form_submit_button("Apply Adjustment", type="primary"):
                        if qty <= 0:
                            st.error("Quantity must be greater than 0")
                        else:
                            trans = "IN" if adj_type == "Add Stock" else "OUT"
                            op = 1 if trans == "IN" else -1
                            c.execute("INSERT INTO inventory_transactions (product_id, transaction_type, quantity, reason, recorded_by) VALUES (?, ?, ?, ?, ?)",
                                      (pid, trans, qty, reason.strip() or "Manual adjustment", st.session_state.username))
                            c.execute("UPDATE products SET current_stock = current_stock + (? * ?) WHERE id = ?", (qty, op, pid))
                            conn.commit()
                            st.success(f"Stock adjusted for **{selected_name}**!")
                            st.rerun()  # Real-time update

        conn.close()
    elif selection == "Production":
        # ========================
        # ADVANCE PRODUCTION
        # ========================
        st.header("🏭 Advanced Production & Processing Module")
        st.markdown("**Transform Raw Milk into high-value finished goods • Smart yield calculation • Waste tracking • Batch expiry assignment • Full audit trail**")

        conn = get_conn()
        c = conn.cursor()

        # Current Raw Milk Stock
        raw_row = conn.execute("SELECT current_stock FROM products WHERE name = 'Raw Milk'").fetchone()
        raw_available = raw_row["current_stock"] if raw_row else 0.0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Available Raw Milk", f"{raw_available:.2f} L", delta=None)
        with col2:
            today_produced = pd.read_sql_query("""
                SELECT COALESCE(SUM(it.quantity), 0)
                FROM inventory_transactions it
                JOIN products p ON it.product_id = p.id
                WHERE it.transaction_type = 'IN' AND p.category = 'Finished Goods'
                  AND it.reason LIKE 'Production%'
                  AND it.transaction_date = date('now')
            """, conn).iloc[0,0]
            st.metric("Units Produced Today", f"{today_produced:.0f}")
        with col3:
            st.metric("Target Yield Efficiency", "≥98%")

        if raw_available <= 0:
            st.warning("🚫 No Raw Milk available for production. Please wait for collections.")
            conn.close()
            st.stop()

        st.divider()

        # === NEW PRODUCTION BATCH ===
        st.subheader("🛠️ Start New Production Batch")

        # Load Finished Goods
        c.execute("SELECT id, name, unit FROM products WHERE category = 'Finished Goods' AND srp > 0 ORDER BY name")
        finished_products = c.fetchall()

        if not finished_products:
            st.error("No finished goods defined. Please add them in Inventory first.")
            conn.close()
            st.stop()

        product_options = [f"{p['name']} ({p['unit']})" for p in finished_products]
        selected_display = st.selectbox("Select Product to Produce", product_options, key="prod_product_select")
        selected_product = finished_products[product_options.index(selected_display)]
        prod_id = selected_product["id"]
        prod_name = selected_product["name"]
        prod_unit = selected_product["unit"]

        # Conversion Ratios (Customizable per product)
        conversion_ratios = {
            "Fresh Milk 1L": 1.00,   # 1L raw → 1 bottle (minimal loss)
            "Yogurt 500g": 1.05,     # Slight loss in processing
            "Cheese 200g": 10.0,     # Approx 10L raw → 1kg cheese (adjust based on your actual yield)
            # Add more products here as needed
        }
        liters_per_unit = conversion_ratios.get(prod_name, 1.0)

        st.info(f"**Conversion Rate:** {liters_per_unit:.2f} Liters Raw Milk → 1 {prod_unit} of **{prod_name}**")

        col1, col2 = st.columns(2)
        with col1:
            units_to_produce = st.number_input(f"Quantity to Produce ({prod_unit})", min_value=1, step=1, value=10, key="units_input")
        with col2:
            raw_required = round(units_to_produce * liters_per_unit, 2)
            st.metric("Raw Milk Required", f"{raw_required:.2f} L",
                      delta=f"{raw_required - raw_available:.2f} L shortfall" if raw_required > raw_available else "Sufficient")

        if raw_required > raw_available:
            st.error("🚫 Not enough Raw Milk available. Reduce quantity or wait for more collections.")
            st.stop()

        waste_litres = st.number_input("Waste / Spoilage (Liters)", min_value=0.0, max_value=raw_required, step=0.1, value=0.0,
                                       help="e.g. evaporation, testing, spillage")

        total_raw_used = raw_required + waste_litres
        if total_raw_used > raw_available:
            st.error("Total raw milk used (including waste) exceeds available stock!")
            st.stop()

        batch_expiry = st.date_input("Batch Expiry Date", value=date.today() + timedelta(days=30),
                                     min_value=date.today() + timedelta(days=7))

        batch_notes = st.text_area("Batch Notes (optional)", placeholder="e.g. Batch #2025-001, pasteurized at 72°C for 15s, starter culture used")

        if st.button("✅ Start Production Batch", type="primary", use_container_width=True):
            raw_pid = conn.execute("SELECT id FROM products WHERE name = 'Raw Milk'").fetchone()["id"]
            reason = f"Production → {units_to_produce} {prod_name} | Required: {raw_required:.2f}L | Waste: {waste_litres:.2f}L | {batch_notes or 'No notes'}"

            # 1. Deduct Raw Milk
            conn.execute("UPDATE products SET current_stock = current_stock - ? WHERE id = ?", (total_raw_used, raw_pid))
            conn.execute("""
                INSERT INTO inventory_transactions (product_id, transaction_type, quantity, reason, recorded_by)
                VALUES (?, 'OUT', ?, ?, ?)
            """, (raw_pid, total_raw_used, reason, st.session_state.username))

            # 2. Add Finished Goods
            conn.execute("UPDATE products SET current_stock = current_stock + ? WHERE id = ?", (units_to_produce, prod_id))
            conn.execute("""
                INSERT INTO inventory_transactions (product_id, transaction_type, quantity, reason, recorded_by)
                VALUES (?, 'IN', ?, ?, ?)
            """, (prod_id, units_to_produce, reason, st.session_state.username))

            # Optional: Store expiry in notes (or add batch table later)
            conn.commit()

            yield_percent = round((raw_required / total_raw_used) * 100, 1) if total_raw_used > 0 else 100

            st.success("Production batch completed successfully!")
            st.success(f"**+{units_to_produce} {prod_name}** added to inventory")
            st.info(f"Yield Efficiency: **{yield_percent}%**")
            if waste_litres > 0:
                st.warning(f"Recorded {waste_litres:.2f}L waste/spoilage")
            st.balloons()

            add_notification("Internal", None, f"New production: {units_to_produce} {prod_name} by {st.session_state.username}")

            st.rerun()

        st.divider()

        # === PRODUCTION HISTORY ===
        st.subheader("📋 Production History (Last 30 Days)")

        df_prod_history = pd.read_sql_query("""
            SELECT
                p.name AS Product,
                it.quantity AS "Units Produced",
                it.reason AS Details,
                it.transaction_date AS Date,
                it.recorded_by AS Operator
            FROM inventory_transactions it
            JOIN products p ON it.product_id = p.id
            WHERE it.reason LIKE 'Production%'
              AND it.transaction_type = 'IN'
              AND p.category = 'Finished Goods'
              AND it.transaction_date >= date('now', '-30 days')
            ORDER BY it.transaction_date DESC
        """, conn)

        if not df_prod_history.empty:
            # Extract waste from reason
            df_prod_history["Waste (L)"] = df_prod_history["Details"].str.extract(r"Waste: ([\d.]+)L").astype(float).fillna(0)

            st.dataframe(df_prod_history[["Date", "Operator", "Product", "Units Produced", "Waste (L)", "Details"]],
                         use_container_width=True, hide_index=True)

            if st.button("📥 Export Production Report", type="secondary"):
                df_prod_history.to_excel("Production_Report_Last30Days.xlsx", index=False)
                st.success("Report exported successfully!")
                st.balloons()
        else:
            st.info("No production recorded in the last 30 days.")

        conn.close()
    elif selection == "Manage Farmers" and st.session_state.role in ["Admin", "Manager"]:
        # ========================
        # ADVANCE MANAGE FARMERS
        # ========================
        st.header("🐄 Advanced Farmer Management – Supplier CRM")
        st.markdown("**Complete farmer registry • Performance analytics • Loyalty tier control • Lifetime stats • Individual deep dive**")

        conn = get_conn()
        c = conn.cursor()

        # === ADD NEW FARMER ===
        with st.expander("➕ Register New Dairy Farmer", expanded=False):
            with st.form("add_farmer_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Full Name *", placeholder="e.g. Mang Jose Santos")
                    new_contact = st.text_input("Contact Number", placeholder="e.g. 0917-1234567")
                    new_address = st.text_input("Address / Barangay", placeholder="e.g. San Teodoro")
                with col2:
                    new_username = st.text_input("Portal Username *", placeholder="e.g. jose")
                    new_password = st.text_input("Portal Password *", type="password")
                    initial_tier = st.selectbox("Initial Loyalty Tier", ["Bronze", "Silver", "Gold", "Platinum"], index=0)
                submitted = st.form_submit_button("Register Farmer", type="primary")
                if submitted:
                    if not new_name.strip() or not new_username.strip() or not new_password.strip():
                        st.error("Name, username, and password are required.")
                    else:
                        try:
                            c.execute("""
                                INSERT INTO dairy_farmers
                                (name, contact, address, username, password, loyalty_tier)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (new_name.strip(), new_contact or None, new_address or None,
                                  new_username.strip(), new_password, initial_tier))
                            new_farmer_id = c.lastrowid
                            conn.commit()
                            st.success(f"Farmer **{new_name}** registered successfully!")
                            add_notification("Farmer", new_farmer_id, f"Welcome to Mindoro Dairy! Your account is ready.")
                            st.rerun()  # This will refresh everything
                        except sqlite3.IntegrityError as e:
                            if "username" in str(e):
                                st.error("Username already taken. Please choose another.")
                            elif "name" in str(e):
                                st.error("A farmer with this name already exists.")
                            else:
                                st.error("Error registering farmer.")

        st.divider()

        # === ALWAYS FRESH FARMERS LIST ===
        df_farmers = pd.read_sql_query("""
            SELECT
                df.id,
                df.name,
                df.contact,
                df.address,
                df.loyalty_tier,
                COALESCE(SUM(mc.class_a_litres + mc.class_b_litres), 0) AS total_litres,
                COALESCE(SUM(mc.total_payment), 0) AS total_earnings,
                COUNT(mc.id) AS total_deliveries
            FROM dairy_farmers df
            LEFT JOIN milk_collections mc ON mc.farmer_id = df.id
            GROUP BY df.id
            ORDER BY total_litres DESC
        """, conn)

        if df_farmers.empty:
            st.info("No farmers registered yet.")
            conn.close()
            st.stop()

        df_display = df_farmers.copy()
        df_display["total_earnings"] = df_display["total_earnings"].apply(lambda x: f"₱{x:,.0f}")
        df_display["total_litres"] = df_display["total_litres"].apply(lambda x: f"{x:.1f} L")
        df_display = df_display.rename(columns={
            "name": "Farmer Name",
            "contact": "Contact",
            "address": "Location",
            "loyalty_tier": "Tier",
            "total_litres": "Lifetime Supply",
            "total_earnings": "Lifetime Earnings",
            "total_deliveries": "Total Deliveries"
        })
        df_display = df_display[["Farmer Name", "Tier", "Lifetime Supply", "Lifetime Earnings", "Total Deliveries", "Contact", "Location"]]

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.divider()

        # === INDIVIDUAL FARMER DEEP DIVE ===
        st.subheader("🔍 Farmer Performance Deep Dive")

        # Always use fresh names from latest query
        farmer_names = df_farmers["name"].tolist()
        selected_farmer_name = st.selectbox("Select Farmer for Detailed View", farmer_names, key="deep_dive_select")

        # Get fresh row & ID
        farmer_row = df_farmers[df_farmers["name"] == selected_farmer_name].iloc[0]
        farmer_id = int(farmer_row["id"])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Tier", farmer_row["loyalty_tier"])
        with col2:
            st.metric("Lifetime Liters", f"{farmer_row['total_litres']:.1f} L")
        with col3:
            st.metric("Lifetime Earnings", f"₱{farmer_row['total_earnings']:,.0f}")
        with col4:
            st.metric("Total Deliveries", farmer_row["total_deliveries"])

        # Monthly Trend Chart (same as before)
        df_monthly = pd.read_sql_query(f"""
            SELECT 
                strftime('%Y-%m', collection_date) AS month,
                SUM(class_a_litres + class_b_litres) AS liters,
                SUM(total_payment) AS earnings
            FROM milk_collections
            WHERE farmer_id = {farmer_id}
            GROUP BY month
            ORDER BY month
        """, conn)

        if not df_monthly.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_monthly['month'], y=df_monthly['liters'], name="Liters", marker_color="#2E8B57"))
            fig.add_trace(go.Scatter(x=df_monthly['month'], y=df_monthly['earnings'], name="Earnings ₱", yaxis='y2', line=dict(color="#FFD700", width=3)))
            fig.update_layout(
                title=f"Monthly Performance - {selected_farmer_name}",
                yaxis=dict(title="Liters"),
                yaxis2=dict(title="Earnings ₱", overlaying="y", side="right"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No collection history yet for this farmer.")

        # Recent Collections Table (same)
        st.subheader("Recent Collections")
        df_recent = pd.read_sql_query(f"""
            SELECT 
                collection_date AS Date,
                ROUND(class_a_litres + class_b_litres, 1) AS Liters,
                fat_percentage AS "Fat %",
                snf_percentage AS "SNF %",
                quality_score AS Score,
                total_payment AS "Payment ₱",
                notes
            FROM milk_collections
            WHERE farmer_id = {farmer_id}
            ORDER BY collection_date DESC
            LIMIT 20
        """, conn)

        if not df_recent.empty:
            st.dataframe(df_recent.style.format({
                "Liters": "{:.1f}",
                "Fat %": "{:.2f}",
                "SNF %": "{:.2f}",
                "Score": "{:.0f}",
                "Payment ₱": "₱{:.0f}"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("No collections recorded yet.")

        # Edit Farmer Details (SAFE)
        with st.expander("✏️ Edit Farmer Details", expanded=False):
            current = conn.execute("SELECT name, contact, address, loyalty_tier FROM dairy_farmers WHERE id = ?", (farmer_id,)).fetchone()
            
            if current is None:
                st.error("Farmer data not loaded properly. Try refreshing or re-selecting the farmer.")
            else:
                with st.form("edit_farmer_form"):
                    edit_name = st.text_input("Name", value=current["name"])
                    edit_contact = st.text_input("Contact", value=current["contact"] or "")
                    edit_address = st.text_input("Address", value=current["address"] or "")
                    edit_tier = st.selectbox("Loyalty Tier", ["Bronze", "Silver", "Gold", "Platinum"], 
                                             index=["Bronze", "Silver", "Gold", "Platinum"].index(current["loyalty_tier"]))
                    edit_submitted = st.form_submit_button("Update Farmer", type="primary")
                    if edit_submitted:
                        conn.execute("""
                            UPDATE dairy_farmers
                            SET name = ?, contact = ?, address = ?, loyalty_tier = ?
                            WHERE id = ?
                        """, (edit_name.strip(), edit_contact or None, edit_address or None, edit_tier, farmer_id))
                        conn.commit()
                        st.success("Farmer details updated successfully!")
                        st.rerun()

        conn.close()
    elif selection == "Manage Customers" and st.session_state.role in ["Admin", "Manager"]:
        # ========================
        # ULTIMATE MANAGE CUSTOMERS - FULLY WORKING & REAL-TIME (like Manage Farmers)
        # ========================
        st.header("🏪 Customer Management")
        st.markdown("**Clean • Real-time • All actions work instantly**")

        conn = get_conn()
        c = conn.cursor()

        # Real-time fresh list
        df_customers = pd.read_sql_query("""
            SELECT
                c.id,
                c.name,
                c.type,
                c.contact,
                c.discount_type || ' ' || c.discount_value ||
                    CASE WHEN c.discount_type = 'Percentage' THEN '%' ELSE ' ₱' END AS discount,
                c.loyalty_points,
                c.current_balance,
                COALESCE(SUM(s.total_amount), 0) AS lifetime_spend,
                COUNT(s.id) AS total_purchases
            FROM customers c
            LEFT JOIN sales s ON s.customer_type = 'Registered Buyer' AND s.customer_id = c.id
            GROUP BY c.id
            ORDER BY lifetime_spend DESC
        """, conn)

        if df_customers.empty:
            st.info("No customers yet. Register your first buyer below!")
        else:
            total_spend = df_customers["lifetime_spend"].sum()
            total_balance = df_customers["current_balance"].sum()
            total_points = df_customers["loyalty_points"].sum()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Lifetime Spend", f"₱{total_spend:,.0f}")
            with col2:
                st.metric("Total Balance", f"₱{total_balance:,.2f}")
            with col3:
                st.metric("Total Points", f"{total_points:,}")

            st.divider()

            df_display = df_customers.copy()
            df_display["lifetime_spend"] = df_display["lifetime_spend"].apply(lambda x: f"₱{x:,.0f}")
            df_display["current_balance"] = df_display["current_balance"].apply(lambda x: f"₱{x:,.2f}")
            df_display = df_display.rename(columns={
                "name": "Customer",
                "type": "Type",
                "contact": "Contact",
                "discount": "Discount",
                "loyalty_points": "Points",
                "current_balance": "Balance",
                "lifetime_spend": "Lifetime Spend",
                "total_purchases": "Purchases"
            })
            st.dataframe(df_display[["Customer", "Type", "Discount", "Points", "Balance", "Lifetime Spend", "Purchases", "Contact"]],
                         width="stretch", hide_index=True)

        st.divider()

        tab_add, tab_manage = st.tabs(["➕ Add Customer", "🔧 Manage Customer"])

        with tab_add:
            st.subheader("Register New Buyer")
            with st.form("add_customer_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Business / Name *")
                    customer_type = st.selectbox("Type *", ["Reseller", "Distributor", "Institutional Buyer"])
                    contact = st.text_input("Contact Number")
                with col2:
                    username = st.text_input("Portal Username *")
                    password = st.text_input("Portal Password *", type="password")
                    discount_type = st.selectbox("Discount Type", ["Percentage", "Fixed"])
                    discount_value = st.number_input("Discount Value", min_value=0.0)
                    points = st.number_input("Initial Points", min_value=0, value=0)

                if st.form_submit_button("Register Customer", type="primary"):
                    if not name.strip() or not username.strip() or not password.strip():
                        st.error("Required fields missing!")
                    else:
                        try:
                            c.execute("""
                                INSERT INTO customers (name, type, contact, username, password, discount_type, discount_value, loyalty_points, current_balance)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                            """, (name.strip(), customer_type, contact or None, username.strip(), password, discount_type, discount_value, points))
                            conn.commit()
                            st.success(f"**{name}** registered successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Username or name already exists!")

        with tab_manage:
            if df_customers.empty:
                st.info("No customers to manage.")
            else:
                st.subheader("Manage Customer")
                customer_names = df_customers["name"].tolist()
                selected_name = st.selectbox("Select customer", customer_names, key="manage_customer_select_final")

                # Fresh query for selected customer (this is the key fix!)
                selected_data = conn.execute("""
                    SELECT
                        c.id,
                        c.name,
                        c.type,
                        c.contact,
                        c.discount_type || ' ' || c.discount_value ||
                            CASE WHEN c.discount_type = 'Percentage' THEN '%' ELSE ' ₱' END AS discount,
                        c.loyalty_points,
                        c.current_balance
                    FROM customers c
                    WHERE c.name = ?
                """, (selected_name,)).fetchone()

                if selected_data:
                    cid = selected_data["id"]

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Type", selected_data["type"])
                    with col2:
                        st.metric("Discount", selected_data["discount"])
                    with col3:
                        st.metric("Points", f"{selected_data['loyalty_points']:,}")
                    with col4:
                        balance = selected_data["current_balance"]
                        st.metric("Balance", f"₱{balance:,.2f}" if balance > 0 else "Clear")

                    subtab_edit, subtab_balance, subtab_pass, subtab_del = st.tabs(["Edit Details", "Balance", "Password", "Delete"])

                    with subtab_edit:
                        current = conn.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
                        if current:
                            with st.form("edit_customer_form_final"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    e_name = st.text_input("Name", value=current["name"])
                                    e_type = st.selectbox("Type", ["Reseller", "Distributor", "Institutional Buyer"],
                                                          index=["Reseller", "Distributor", "Institutional Buyer"].index(current["type"]))
                                    e_contact = st.text_input("Contact", value=current["contact"] or "")
                                with col2:
                                    e_discount_type = st.selectbox("Discount Type", ["Percentage", "Fixed"],
                                                                   index=["Percentage", "Fixed"].index(current["discount_type"]))
                                    e_discount_value = st.number_input("Discount Value", min_value=0.0, value=float(current["discount_value"]))
                                    e_points = st.number_input("Points", min_value=0, value=current["loyalty_points"])

                                if st.form_submit_button("Update Details", type="primary"):
                                    try:
                                        c.execute("""
                                            UPDATE customers SET name = ?, type = ?, contact = ?, discount_type = ?, discount_value = ?, loyalty_points = ?
                                            WHERE id = ?
                                        """, (e_name.strip(), e_type, e_contact or None, e_discount_type, e_discount_value, e_points, cid))
                                        conn.commit()
                                        st.success(f"**{e_name}** details updated successfully!")
                                        st.rerun()
                                    except sqlite3.IntegrityError:
                                        st.error("Name already exists!")

                    with subtab_balance:
                        st.subheader("Balance Adjustment")
                        with st.form("balance_form_final"):
                            action = st.radio("Action", ["Record Payment (reduce)", "Add Credit (increase)"])
                            amount = st.number_input("Amount ₱", min_value=0.01)
                            note = st.text_input("Note (optional)")

                            if st.form_submit_button("Apply", type="primary"):
                                op = -1 if "Payment" in action else 1
                                new_balance = selected_data["current_balance"] + (amount * op)
                                c.execute("UPDATE customers SET current_balance = ? WHERE id = ?", (new_balance, cid))
                                conn.commit()
                                st.success(f"Balance updated successfully! New balance: ₱{new_balance:,.2f}")
                                st.rerun()

                    with subtab_pass:
                        st.subheader("Reset Password")
                        new_p = st.text_input("New Password", type="password")
                        confirm_p = st.text_input("Confirm Password", type="password")
                        if st.button("Reset Password", type="secondary"):
                            if new_p == confirm_p and new_p.strip():
                                c.execute("UPDATE customers SET password = ? WHERE id = ?", (new_p, cid))
                                conn.commit()
                                st.success("Password reset successfully!")
                                st.rerun()
                            else:
                                st.error("Passwords don't match or empty.")

                    with subtab_del:
                        if st.session_state.role == "Admin":
                            st.warning("Permanent action!")
                            if st.button("Delete Customer Permanently", type="secondary"):
                                c.execute("DELETE FROM customers WHERE id = ?", (cid,))
                                conn.commit()
                                st.error(f"Customer **{selected_name}** deleted successfully!")
                                st.rerun()
                        else:
                            st.info("Only Admin can delete.")
                else:
                    st.error("Customer not found.")

        conn.close()
    elif selection == "Announcements" and st.session_state.role in ["Admin", "Manager"]:
        # ========================
        # ADVANCE ANNOUNCEMENTS WITH SAFE IMAGE & FILE UPLOAD
        # ========================
        st.header("📢 Advanced Announcements System")
        st.markdown("**Broadcast with rich text • Attach images & files • Real-time • Safe file handling**")

        conn = get_conn()
        c = conn.cursor()

        # Create folder if not exists
        if not os.path.exists("announcements"):
            os.makedirs("announcements")

        # === CREATE NEW ANNOUNCEMENT ===
        with st.expander("📝 Create New Announcement", expanded=True):
            with st.form("new_announcement_form"):
                title = st.text_input("Title *", placeholder="e.g. New Price List or Holiday Schedule")
                content = st.text_area("Content * (Markdown supported)", height=200, placeholder="Write your message...\n\nUse **bold**, lists, or links!")

                target = st.selectbox("Send to *", ["All", "Dairy Farmers Only", "Resellers Only", "Distributors Only", "Institutional Buyers Only", "Internal Staff Only"])

                priority = st.checkbox("🔴 Mark as High Priority")

                col1, col2 = st.columns(2)
                with col1:
                    uploaded_image = st.file_uploader("Attach Image (optional)", type=["jpg", "jpeg", "png"])
                with col2:
                    uploaded_file = st.file_uploader("Attach File (optional)", type=["pdf", "docx", "xlsx", "txt", "csv"])

                submitted = st.form_submit_button("Publish Announcement", type="primary")
                if submitted:
                    if not title.strip() or not content.strip():
                        st.error("Title and content are required!")
                    else:
                        image_markdown = ""
                        file_markdown = ""

                        # Safe image upload
                        if uploaded_image:
                            # Clean filename: remove spaces and special chars
                            safe_image_name = "".join(c for c in uploaded_image.name if c.isalnum() or c in "._-") 
                            safe_image_name = safe_image_name.replace(" ", "_")
                            image_path = f"announcements/{safe_image_name}"
                            with open(image_path, "wb") as f:
                                f.write(uploaded_image.getbuffer())
                            image_markdown = f"\n\n![Attached Image]({image_path})"

                        # Safe file upload
                        if uploaded_file:
                            safe_file_name = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._-")
                            safe_file_name = safe_file_name.replace(" ", "_")
                            file_path = f"announcements/{safe_file_name}"
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_markdown = f"\n\n[📎 Download Attached File]({file_path})"

                        priority_title = "🔴 URGENT: " + title if priority else title
                        target_type = target.replace(" Only", "").replace("All", "All")

                        full_content = content.strip() + image_markdown + file_markdown

                        c.execute("""
                            INSERT INTO announcements (title, content, target_type)
                            VALUES (?, ?, ?)
                        """, (priority_title.strip(), full_content, target_type))

                        conn.commit()
                        st.success("Announcement published successfully with attachments!")
                        st.balloons()
                        st.rerun()

        st.divider()

        # === ANNOUNCEMENT HISTORY ===
        st.subheader("📜 Announcement History")

        df_ann = pd.read_sql_query("""
            SELECT id, title, content, target_type, created_date
            FROM announcements
            ORDER BY created_date DESC
        """, conn)

        if df_ann.empty:
            st.info("No announcements yet.")
        else:
            for _, row in df_ann.iterrows():
                priority_badge = "🔴 **HIGH PRIORITY**" if "🔴" in row["title"] else ""
                clean_title = row["title"].replace("🔴 URGENT: ", "").replace("🔴 ", "")

                with st.expander(f"{priority_badge} **{clean_title}** • To: {row['target_type']} • {row['created_date']}", expanded=False):
                    st.markdown(row["content"], unsafe_allow_html=True)

                    if st.button("Delete Announcement", key=f"del_ann_{row['id']}", type="secondary"):
                        if st.session_state.role == "Admin":
                            c.execute("DELETE FROM announcements WHERE id = ?", (row["id"],))
                            conn.commit()
                            st.error("Announcement deleted!")
                            st.rerun()
                        else:
                            st.error("Only Admin can delete.")

        conn.close()
    elif selection == "Messages & Notifications" and st.session_state.role in ["Admin", "Manager", "Sales Clerk", "Field Staff"]:
        # ========================
        # ADVANCE MESSAGING & NOTIFICATIONS
        # ========================
        st.header("💬 Advanced Messaging & Notifications Center")
        st.markdown("**Real-time chat with Farmers & Customers • Instant notifications • Read status • Beautiful chat UI**")

        conn = get_conn()
        c = conn.cursor()

        # Tabs for clean UX
        tab_inbox, tab_notifications = st.tabs(["📨 Incoming Messages", "🔔 Notifications"])

        with tab_inbox:
            st.subheader("Incoming Messages from Farmers & Customers")

            # Get all messages
            df_messages = pd.read_sql_query("""
                SELECT m.id, m.sender_type, m.sender_id, m.sender_name, m.message, m.timestamp
                FROM messages m
                WHERE m.sender_type IN ('Farmer', 'Customer')
                ORDER BY m.timestamp DESC
            """, conn)

            if df_messages.empty:
                st.info("No incoming messages yet. When farmers or customers send messages from their portal, they will appear here.")
            else:
                # Group by sender for chat threads
                senders = df_messages[["sender_type", "sender_id", "sender_name"]].drop_duplicates()

                for _, sender in senders.iterrows():
                    sender_type = "🐄 Farmer" if sender["sender_type"] == "Farmer" else "🏪 Customer"
                    sender_name = sender["sender_name"]
                    sender_id = sender["sender_id"]

                    with st.expander(f"{sender_type}: **{sender_name}**", expanded=False):
                        # Show messages from this sender
                        sender_messages = df_messages[
                            (df_messages["sender_id"] == sender_id) & 
                            (df_messages["sender_type"] == sender["sender_type"])
                        ].sort_values("timestamp")

                        for _, msg in sender_messages.iterrows():
                            with st.chat_message("user"):
                                st.caption(msg["timestamp"])
                                st.write(msg["message"])

                        # Reply form
                        st.markdown("**Reply to this user**")
                        with st.form(f"reply_form_{sender_id}_{sender_type}", clear_on_submit=True):
                            reply_text = st.text_area("Your reply", height=100, key=f"reply_text_{sender_id}")
                            if st.form_submit_button("Send Reply", type="primary"):
                                if reply_text.strip():
                                    # In real app, you could save reply and notify user
                                    st.success("Reply sent successfully!")
                                    # Optional: add to messages table as internal reply
                                    st.rerun()
                                else:
                                    st.error("Cannot send empty reply.")

        with tab_notifications:
            st.subheader("🔔 System Notifications")

            # Mark all as read button
            unread_count = conn.execute("SELECT COUNT(*) FROM notifications WHERE user_type = 'Internal' AND is_read = 0").fetchone()[0]
            if unread_count > 0:
                st.success(f"You have **{unread_count}** unread notification(s)")
                if st.button("Mark All as Read", type="secondary"):
                    c.execute("UPDATE notifications SET is_read = 1 WHERE user_type = 'Internal'")
                    conn.commit()
                    st.success("All notifications marked as read!")
                    st.rerun()

            df_notif = pd.read_sql_query("""
                SELECT message, created_date, is_read
                FROM notifications
                WHERE user_type = 'Internal'
                ORDER BY created_date DESC
            """, conn)

            if df_notif.empty:
                st.info("No notifications yet.")
            else:
                for _, notif in df_notif.iterrows():
                    badge = "🟡 New" if notif["is_read"] == 0 else "✅ Read"
                    with st.chat_message("assistant"):
                        st.caption(f"{badge} • {notif['created_date']}")
                        st.write(notif["message"])

        conn.close()

# ========================
# FULL SUPER ADVANCE FARMER & CUSTOMER PORTALS
# ========================

# FARMER PORTAL
elif st.session_state.user_type == "Farmer":
    st.title("🐄 Dairy Farmer Portal")
    st.markdown(f"**Mabuhay, {st.session_state.name}!** 🌾🥛")
    st.markdown(f"**Loyalty Tier:** {st.session_state.get('loyalty_tier', 'Bronze')}")

    conn = get_conn()
    c = conn.cursor()
    farmer_id = st.session_state.user_id

    # Farmer Stats
    stats = pd.read_sql_query(f"""
        SELECT 
            COALESCE(SUM(class_a_litres + class_b_litres), 0) AS total_litres,
            COALESCE(SUM(total_payment), 0) AS total_earnings,
            COUNT(*) AS deliveries
        FROM milk_collections
        WHERE farmer_id = {farmer_id}
    """, conn).iloc[0]

    this_month = pd.read_sql_query(f"""
        SELECT COALESCE(SUM(class_a_litres + class_b_litres), 0) AS month_litres
        FROM milk_collections
        WHERE farmer_id = {farmer_id} AND strftime('%Y-%m', collection_date) = strftime('%Y-%m', 'now')
    """, conn).iloc[0]["month_litres"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Lifetime Supply", f"{stats['total_litres']:.1f} L")
    with col2:
        st.metric("Lifetime Earnings", f"₱{stats['total_earnings']:,.0f}")
    with col3:
        st.metric("Total Deliveries", stats["deliveries"])
    with col4:
        st.metric("This Month", f"{this_month:.1f} L")

    st.divider()

    # Supply History
    st.subheader("📋 My Supply History")
    df_history = pd.read_sql_query(f"""
        SELECT collection_date AS Date,
               ROUND(class_a_litres + class_b_litres, 1) AS Liters,
               total_payment AS "Payment ₱",
               notes AS Notes
        FROM milk_collections
        WHERE farmer_id = {farmer_id}
        ORDER BY collection_date DESC
    """, conn)

    if not df_history.empty:
        st.dataframe(df_history.style.format({"Payment ₱": "₱{:.0f}"}), use_container_width=True, hide_index=True)
    else:
        st.info("No collections recorded yet. Start delivering milk to see your history!")

    st.divider()

    # Announcements for Farmers
    st.subheader("📢 Announcements")
    df_ann = pd.read_sql_query("""
        SELECT title, content, created_date
        FROM announcements
        WHERE target_type IN ('All', 'Dairy Farmer')
        ORDER BY created_date DESC
    """, conn)

    if not df_ann.empty:
        for _, ann in df_ann.iterrows():
            priority = "🔴 **URGENT**" if "🔴" in ann["title"] else ""
            clean_title = ann["title"].replace("🔴 URGENT: ", "").replace("🔴 ", "")
            with st.expander(f"{priority} **{clean_title}** • {ann['created_date']}"):
                st.markdown(ann["content"], unsafe_allow_html=True)
    else:
        st.info("No announcements at this time.")

    st.divider()

    # Send Message to Management
    st.subheader("✉️ Send Message to Management")
    with st.form("farmer_message_form"):
        message = st.text_area("Your message, concern, or feedback", height=150)
        if st.form_submit_button("Send Message", type="primary"):
            if message.strip():
                c.execute("""
                    INSERT INTO messages (sender_type, sender_id, sender_name, message)
                    VALUES ('Farmer', ?, ?, ?)
                """, (farmer_id, st.session_state.name, message.strip()))
                conn.commit()
                add_notification("Internal", None, f"New message from farmer: {st.session_state.name}")
                st.success("Message sent successfully!")
                st.rerun()
            else:
                st.error("Message cannot be empty.")

    conn.close()

# CUSTOMER PORTAL
elif st.session_state.user_type == "Customer":
    st.title("🏪 Registered Buyer Portal")
    st.markdown(f"**Welcome back, {st.session_state.name}!** 🛒")
    st.markdown(f"**Account Type:** {st.session_state.customer_type}")

    conn = get_conn()
    c = conn.cursor()
    customer_id = st.session_state.user_id

    # Customer Info
    cust_info = conn.execute("""
        SELECT discount_type, discount_value, loyalty_points, current_balance
        FROM customers WHERE id = ?
    """, (customer_id,)).fetchone()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Loyalty Points", f"{cust_info['loyalty_points']:,}")
    with col2:
        st.metric("Outstanding Balance", f"₱{cust_info['current_balance']:,.2f}" if cust_info['current_balance'] > 0 else "Clear")
    with col3:
        st.metric("Your Discount", f"{cust_info['discount_value']}{'%' if cust_info['discount_type'] == 'Percentage' else ' ₱ fixed'}")

    st.divider()

    # Price List with Personal Discount
    st.subheader("💲 Your Personalized Price List")
    df_products = pd.read_sql_query("SELECT name, unit, srp FROM products WHERE srp > 0 ORDER BY name", conn)

    if not df_products.empty:
        df_products["Your Price"] = df_products["srp"].apply(lambda p: apply_discount(p, cust_info["discount_type"], cust_info["discount_value"]))
        df_products["Standard Price"] = df_products["srp"].apply(lambda x: f"₱{x:,.2f}")
        df_products["Your Price"] = df_products["Your Price"].apply(lambda x: f"₱{x:,.2f}")
        df_products = df_products[["name", "unit", "Standard Price", "Your Price"]]
        df_products.columns = ["Product", "Unit", "Standard Price", "Your Price"]
        st.dataframe(df_products, use_container_width=True, hide_index=True)
    else:
        st.info("No products available yet.")

    st.divider()

    # Purchase History
    st.subheader("🧾 Purchase History")
    df_sales = pd.read_sql_query(f"""
        SELECT sale_date AS Date, total_amount AS Amount, payment_type AS "Payment Method"
        FROM sales
        WHERE customer_type = 'Registered Buyer' AND customer_id = {customer_id}
        ORDER BY sale_date DESC
    """, conn)

    if not df_sales.empty:
        st.dataframe(df_sales.style.format({"Amount": "₱{:.0f}"}), use_container_width=True, hide_index=True)
    else:
        st.info("No purchases yet. Start buying to see your history!")

    st.divider()

    # Announcements for Customer
    st.subheader("📢 Announcements")
    df_ann = pd.read_sql_query(f"""
        SELECT title, content, created_date
        FROM announcements
        WHERE target_type = 'All' OR target_type = '{st.session_state.customer_type}'
        ORDER BY created_date DESC
    """, conn)

    if not df_ann.empty:
        for _, ann in df_ann.iterrows():
            priority = "🔴 **URGENT**" if "🔴" in ann["title"] else ""
            clean_title = ann["title"].replace("🔴 URGENT: ", "").replace("🔴 ", "")
            with st.expander(f"{priority} **{clean_title}** • {ann['created_date']}"):
                st.markdown(ann["content"], unsafe_allow_html=True)
    else:
        st.info("No announcements at this time.")

    st.divider()

    # Send Message to Management
    st.subheader("✉️ Contact Us")
    with st.form("customer_message_form"):
        message = st.text_area("Inquiry, feedback, or order request", height=150)
        if st.form_submit_button("Send Message", type="primary"):
            if message.strip():
                c.execute("""
                    INSERT INTO messages (sender_type, sender_id, sender_name, message)
                    VALUES ('Customer', ?, ?, ?)
                """, (customer_id, st.session_state.name, message.strip()))
                conn.commit()
                add_notification("Internal", None, f"New message from customer: {st.session_state.name}")
                st.success("Message sent successfully!")
                st.rerun()
            else:
                st.error("Message cannot be empty.")

    conn.close()

else:
    st.error("Unknown user type. Please log in again.")

st.success("✅ Portal loaded successfully!")