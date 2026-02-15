import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
from datetime import datetime

# Import Database Functions
from database import (
    init_db, create_user, authenticate_user, 
    add_expense_db, get_expenses_db, set_initial_balance_db, get_initial_balance_db,
    add_recurring_expense_db, get_recurring_expenses_db, delete_recurring_expense_db,
    add_expense_batch_db, create_session, validate_session, delete_session,
    add_investment_db, get_investments_db, delete_investment_db,
    archive_and_reset_expenses, get_archived_expenses, undo_last_reset
)

# Import AI Logic
from ai_logic import detect_anomalies, predict_month_end, generate_savings_tips, check_recurring_reminders

# Import UI Utils
from ui_utils import get_category_icon, get_custom_css, generate_backup, parse_bank_statement, auto_categorize

# Initialize DB
init_db()

def main():
    st.set_page_config(page_title="Expenses Analysis", page_icon="💰", layout="wide")

    # --- Session State Init ---
    if 'theme' not in st.session_state:
        st.session_state.theme = "Dark"
    
    # --- Apply Theme ---
    st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

    # --- Authentication Check ---
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.username = None

    # Check for session token in URL if not logged in
    if st.session_state.user_id is None:
        try:
            # Try getting session_id from query params (support for both new and old Streamlit versions)
            qp = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
            session_id = qp.get('session_id')
            # Handle if it returns a list (old version) or string (new version)
            if session_id:
                if isinstance(session_id, list): session_id = session_id[0]
                
                uid, uname = validate_session(session_id)
                if uid:
                    st.session_state.user_id = uid
                    st.session_state.username = uname
        except:
            pass # Fail silently if query params feature has issues

    if st.session_state.user_id is None:
        login_page()
    else:
        dashboard_page()


def login_page():
    st.markdown("<h1 style='text-align: center;'>🔐 Secure Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", type="primary")
                
                if submit:
                    user_id = authenticate_user(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        
                        # Create Persistent Session
                        session_id = create_session(user_id)
                        if hasattr(st, "query_params"):
                            st.query_params['session_id'] = session_id
                        else:
                            st.experimental_set_query_params(session_id=session_id)
                            
                        st.success(f"Welcome back, {username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                register = st.form_submit_button("Register")
                
                if register:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match")
                    elif len(new_pass) < 4:
                        st.error("Password must be at least 4 characters")
                    else:
                        if create_user(new_user, new_pass):
                            st.success("Account created! Please login.")
                        else:
                            st.error("Username already exists.")


def dashboard_page():
    # Helper to Navigate
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"

    def navigate_to(page_name):
        st.session_state.page = page_name

    # Sidebar Controls
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}**")
        
        # Theme Toggle
        current_theme = st.session_state.theme
        new_theme = "Light" if current_theme == "Dark" else "Dark"
        btn_label = "☀️ Light Mode" if current_theme == "Dark" else "🌙 Dark Mode"
        
        if st.button(btn_label):
            st.session_state.theme = new_theme
            st.rerun()

        if st.button("Logout"):
            # Clear persistent session
            try:
                qp = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
                session_id = qp.get('session_id')
                if session_id:
                    if isinstance(session_id, list): session_id = session_id[0]
                    delete_session(session_id)
                
                if hasattr(st, "query_params"):
                    st.query_params.clear()
                else:
                    st.experimental_set_query_params()
            except:
                pass

            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.page = "Dashboard"
            st.rerun()

    # Top Navigation Bar
    st.markdown("""
    <div style='text-align: center; margin-bottom: 10px;'>
        <span style='background-color: #4C51BF; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; box-shadow: 0px 4px 6px rgba(0,0,0,0.2);'>
            Made By Aditya
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Expenses Analysis</h1>", unsafe_allow_html=True)
    
    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6, col_nav7, col_nav8, col_nav9 = st.columns(9)
    
    with col_nav1:
        if st.button("Dashboard", use_container_width=True):
            navigate_to("Dashboard")
    with col_nav2:
        if st.button("Insights", use_container_width=True):
            navigate_to("Insights")
    with col_nav3:
        if st.button("Add", use_container_width=True): # Renamed
            navigate_to("Add Expense")
    with col_nav4:
        if st.button("History", use_container_width=True):
            navigate_to("History")
    with col_nav5:
        if st.button("Recurring", use_container_width=True): # New Button
            navigate_to("Recurring")
    with col_nav6:
        if st.button("Investments", use_container_width=True): # New Button
            navigate_to("Investments")
    with col_nav7:
        if st.button("Previous", use_container_width=True): # New Button
            navigate_to("Previous")
    with col_nav8:
        if st.button("Data", use_container_width=True):
            navigate_to("Data")
    with col_nav9:
        if st.button("Settings", use_container_width=True):
            navigate_to("Settings")

    st.divider()

    # Fetch Data for Current User
    user_id = st.session_state.user_id
    expenses = get_expenses_db(user_id)
    initial_balance = get_initial_balance_db(user_id)
    recurring = get_recurring_expenses_db(user_id)
    investments = get_investments_db(user_id) # Fetch investments
    
    # Process Income vs Expenses
    total_income = sum(e['amount'] for e in expenses if e.get('type') == 'income')
    total_spent = sum(e['amount'] for e in expenses if e.get('type') == 'expense')
    
    # Net Worth = Initial + Income - Expenses
    current_balance = initial_balance + total_income - total_spent
    net_worth = current_balance # checks out basically
    
    # Calculate Average Daily (Expenses Only)
    expense_data = [e for e in expenses if e.get('type') == 'expense']
    if expense_data:
        dates = []
        for e in expense_data:
            try:
                # Try full format first
                d = datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                try:
                    # Fallback to just date
                    d = datetime.strptime(e['date'], "%Y-%m-%d").date()
                except ValueError:
                    # Fallback to today if parsing fails entirely, to prevent crash
                    d = datetime.now().date()
            dates.append(d)
            
        first_date = min(dates)
        days_active = (datetime.now().date() - first_date).days + 1
        avg_daily = total_spent / days_active
    else:
        avg_daily = 0.0

    # --- AI Analysis (on Expense Data Only) ---
    anomalies = detect_anomalies(expense_data)
    reminders = check_recurring_reminders(recurring)
    tips = generate_savings_tips(expense_data)

    # Main Content
    if st.session_state.page == "Dashboard":
        
        # --- Smart Alerts Section ---
        if anomalies or reminders:
            with st.expander("🔔 Smart Alerts & Reminders", expanded=True):
                for alert in reminders:
                    st.warning(alert, icon="📅")
                for alert in anomalies:
                    st.error(alert, icon="⚠️")
        

        st.subheader("📊 Financial Overview")
        
        # Health Score Logic
        try:
            savings_ratio = (current_balance / (total_income + initial_balance)) * 100 if (total_income + initial_balance) > 0 else 0
            health_score = min(100, max(0, int(savings_ratio * 1.5))) # Simple logic
        except:
            health_score = 50

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Net Worth (Balance)", f"₹{current_balance:,.2f}", help="Initial + Income - Expenses")
        with col2:
            st.metric("Total Income", f"₹{total_income:,.2f}", delta=f"+₹{total_income:,.2f}", delta_color="normal")
        with col3:
            st.metric("Total Expenses", f"₹{total_spent:,.2f}", delta=f"-₹{total_spent:,.2f}", delta_color="inverse")
        with col4:
            st.metric("Health Score", f"{health_score}/100", delta=("Good" if health_score > 70 else "Needs Work"), help="Based on savings ratio")

        st.markdown("###")

        col_chart1, col_chart2 = st.columns(2)
        
        if expense_data:
            df = pd.DataFrame(expense_data)
            # Add Icons to Category
            df['display_category'] = df['category'].apply(lambda x: f"{get_category_icon(x)} {x}")
            
            with col_chart1:
                st.write("#### Expenses by Category")
                category_data = df.groupby("display_category")["amount"].sum().reset_index()
                
                fig = px.pie(category_data, values='amount', names='display_category', 
                             hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(
                    showlegend=True, 
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#E2E8F0" if st.session_state.theme == "Dark" else "#212529")
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col_chart2:
                st.write("#### Recent Activity")
                # Show mix of income and expense
                full_df = pd.DataFrame(expenses)
                full_df['display_category'] = full_df.apply(lambda x: f"💰 {x['category']}" if x['type'] == 'income' else f"{get_category_icon(x['category'])} {x['category']}", axis=1)
                
                recent_df = full_df[['date', 'display_category', 'amount', 'type']].head(5)
                recent_df.columns = ['Date', 'Category', 'Amount', 'Type']
                
                # Color code type? Streamlit dataframe doesn't support generic row coloring easily, 
                # but we can show it as a column.
                st.dataframe(recent_df, use_container_width=True, hide_index=True)
                
        else:
            st.info("No transaction data found. Use 'Data' page to import CSV or 'Add' to enter manually.")
            
        # Savings Tips
        if tips:
            st.info(tips[0], icon="💡")

    elif st.session_state.page == "Insights":
        st.subheader("📈 Analytics & Insights")
        
        # Forecast
        predicted_total, predicted_savings = predict_month_end(expense_data, current_balance)
        
        with st.container():
            st.markdown("#### 🔮 AI Predictions (Month End)")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.metric("Predicted Total Spend", f"₹{predicted_total:,.2f}", help="Estimated total spend by month end based on current pace")
            with p_col2:
                st.metric("Estimated Savings", f"₹{predicted_savings:,.2f}", delta="Projected", help="Estimated remaining balance")
        
        st.divider()
        
        if expense_data:
            df = pd.DataFrame(expense_data)
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M').astype(str)
            df['day'] = df['date'].dt.date
            df['display_category'] = df['category'].apply(lambda x: f"{get_category_icon(x)} {x}")
            
            # --- Key Insights ---
            st.markdown("#### 💡 Smart Insights")
            col1, col2, col3 = st.columns(3)
            
            # Monthly Comparison
            current_month = datetime.now().strftime('%Y-%m')
            last_month = (datetime.now() - pd.DateOffset(months=1)).strftime('%Y-%m')
            
            this_month_spent = df[df['month'] == current_month]['amount'].sum()
            last_month_spent = df[df['month'] == last_month]['amount'].sum()
            
            diff = this_month_spent - last_month_spent
            delta_color = "inverse" if diff > 0 else "normal" # Red if spent more
            
            with col1:
                st.metric("This Month vs Last", f"₹{this_month_spent:,.2f}", delta=f"₹{diff:,.2f}", delta_color=delta_color)

            # Top Category
            top_cat = df.groupby('display_category')['amount'].sum().idxmax()
            top_cat_amount = df.groupby('display_category')['amount'].sum().max()
            with col2:
                st.metric("Top Spending Category", top_cat, f"₹{top_cat_amount:,.2f}")
                
            # Highest Spending Day
            daily_sum = df.groupby('day')['amount'].sum()
            max_day = daily_sum.idxmax()
            max_day_val = daily_sum.max()
            with col3:
                st.metric("Highest Spending Day", max_day.strftime('%d %b'), f"₹{max_day_val:,.2f}")

            st.divider()
            
            # --- Charts ---
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.write("#### 📅 Daily Spending Trend")
                daily_trend = df.groupby('day')['amount'].sum().reset_index()
                fig_line = px.line(daily_trend, x='day', y='amount', markers=True, 
                                   line_shape='spline', color_discrete_sequence=['#4C51BF'])
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0" if st.session_state.theme == "Dark" else "#212529"))
                st.plotly_chart(fig_line, use_container_width=True)

            with col_chart2:
                st.write("#### 🗓️ Monthly Spending")
                # Stacked Bar: Group by Month AND Category
                monthly_trend = df.groupby(['month', 'display_category'])['amount'].sum().reset_index()
                monthly_trend['amount'] = monthly_trend['amount'].round(2)
                
                fig_bar = px.bar(monthly_trend, x='month', y='amount', color='display_category',
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color="#E2E8F0" if st.session_state.theme == "Dark" else "#212529"),
                    xaxis=dict(type='category'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            # Detailed Breakdown Table
            with st.expander("View Detailed Category Breakdown"):
                cat_month_pivot = df.pivot_table(index='display_category', columns='month', values='amount', aggfunc='sum', fill_value=0)
                st.dataframe(cat_month_pivot, use_container_width=True)

        else:
            st.info("Not enough data to generate insights.")
            
        st.divider()
        st.subheader("⚙️ Manage Monthly Data")
        st.info("Reset your expenses for a new month here. Old data will be archived.")
        
        c_reset1, c_reset2 = st.columns(2)
        with c_reset1:
            if st.button("🔴 Reset Month Expenses", type="primary", use_container_width=True):
                archive_and_reset_expenses(user_id)
                st.success("Month reset successfully! Old data moved to 'Previous'.")
                time.sleep(1)
                st.rerun()
        
        with c_reset2:
            if st.button("↩️ Undo Last Reset", use_container_width=True):
                if undo_last_reset(user_id):
                    st.success("Undo successful! Budget restored.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("No recent reset found to undo.")

    elif st.session_state.page == "Add Expense":
        st.subheader("💸 Add New Transaction")
        
        # Toggle Income/Expense
        tx_type = st.radio("Transaction Type", ["Expense", "Income"], horizontal=True)
        
        with st.container():
            with st.form("expense_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
                    date_val = st.date_input("Date", value="today")
                with col2:
                    if tx_type == "Expense":
                        # Categories with Icons
                        cats = ["Food", "Transport", "Utilities", "Entertainment", "Shopping", "Health", "Education", "Other"]
                        cat_map = {c: f"{get_category_icon(c)} {c}" for c in cats}
                        selected_display = st.selectbox("Category", list(cat_map.values()))
                        category = [k for k, v in cat_map.items() if v == selected_display][0]
                    else:
                        category = st.selectbox("Source", ["Salary", "Business", "Interest", "Gift", "Other"])
                    
                description = st.text_input("Description", placeholder="e.g. Grocery shopping" if tx_type == "Expense" else "e.g. Monthly Salary")
                
                submitted = st.form_submit_button(f"Add {tx_type}", type="primary")
                if submitted:
                    if amount > 0:
                        full_datetime = datetime.combine(date_val, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
                        add_expense_db(user_id, amount, category, description, full_datetime, tx_type.lower())
                        st.toast(f"{tx_type} added successfully!", icon="✅")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Please enter a valid amount.")

    elif st.session_state.page == "History":
        st.subheader("📜 Complete History")
        
        if expenses:
            df = pd.DataFrame(expenses)
            
            # Enhance DF
            df['display_category'] = df.apply(lambda x: f"💰 {x['category']}" if x['type'] == 'income' else f"{get_category_icon(x['category'])} {x['category']}", axis=1)
            
            with st.expander("🔎 Filter Options"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    filter_category = st.multiselect("Filter by Category", df['display_category'].unique())
                with col2:
                    filter_type = st.multiselect("Filter by Type", ["expense", "income"])
            
            if filter_category:
                df = df[df['display_category'].isin(filter_category)]
            
            if filter_type:
                df = df[df['type'].isin(filter_type)]
            
            # Show display_category but keep original for download/logic if needed
            show_df = df[['date', 'display_category', 'description', 'amount', 'type']]
            show_df.columns = ['Date', 'Category', 'Description', 'Amount', 'Type']
            
            # Color amounts differently? 
            # Streamlit doesn't support conditional formatting in basic dataframe easily without styling (Pandas Styler), 
            # but standard view is fine for now.
            st.dataframe(show_df, use_container_width=True, height=500, hide_index=True)
            
            st.download_button(
                label="📥 Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='expenses.csv',
                mime='text/csv',
            )
        else:
            st.info("No transaction history available.")
            
    elif st.session_state.page == "Data":
        st.subheader("💾 Data Management")
        
        tab1, tab2 = st.tabs(["Import CSV", "Backup & Restore"])
        
        with tab1:
            st.write("Upload your bank statement (CSV) to automatically import transactions.")
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            
            if uploaded_file:
                df = parse_bank_statement(uploaded_file)
                if df is not None:
                    st.success("File parsed successfully!")
                    st.write("#### Preview")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("Confirm Import", type="primary"):
                        # Prepare batch list
                        # (user_id, amount, category, description, date, transaction_type)
                        batch = []
                        for _, row in df.iterrows():
                            # Auto Categorize
                            desc = str(row.get('description', ''))
                            cat = auto_categorize(desc)
                            
                            # Determine Type
                            amt = float(row.get('amount', 0))
                            
                            # Default Logic
                            if amt > 0:
                                tx_type = 'income' if cat == 'Salary' else 'expense'
                            else:
                                # Negative amount usually means expense in many exports
                                tx_type = 'expense'
                                amt = abs(amt) # Store as positive
                            
                            # Keyword override for Income
                            income_keywords = ['salary', 'credit', 'interest', 'refund', 'dividend', 'deposit']
                            if any(k in desc.lower() for k in income_keywords):
                                tx_type = 'income'
                                amt = abs(amt)

                            if 'type' in row and pd.notna(row['type']):
                                t = str(row['type']).lower()
                                if 'credit' in t or 'cr' in t or 'income' in t: tx_type = 'income'
                                elif 'debit' in t or 'dr' in t or 'expense' in t: tx_type = 'expense'
                            
                            date_str = str(row.get('date', datetime.now().strftime("%Y-%m-%d")))
                            
                            batch.append((user_id, amt, cat, desc, date_str, tx_type))
                            
                        # --- Auto-Match Initial Balance Logic ---
                        # Calculate net change from this import
                        import_income = sum(x[1] for x in batch if x[5] == 'income')
                        import_expense = sum(x[1] for x in batch if x[5] == 'expense')
                        net_import_change = import_income - import_expense
                        
                        # Get current state
                        current_initial = get_initial_balance_db(user_id)
                        current_txs = get_expenses_db(user_id)
                        curr_income = sum(e['amount'] for e in current_txs if e['type'] == 'income')
                        curr_expense = sum(e['amount'] for e in current_txs if e['type'] == 'expense')
                        current_net = current_initial + curr_income - curr_expense
                        
                        projected_balance = current_net + net_import_change
                        
                        if projected_balance < 0:
                            needed = abs(projected_balance)
                            new_initial = current_initial + needed
                            set_initial_balance_db(user_id, new_initial)
                            st.toast(f"Auto-adjusted Initial Balance by +₹{needed:,.2f} to cover expenses.", icon="⚖️")
                            
                        add_expense_batch_db(batch)
                        st.success(f"Successfully imported {len(batch)} transactions!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Could not parse CSV. Ensure it has 'Date', 'Description', and 'Amount' columns.")
                    
        with tab2:
            st.write("Backup your data or restore from a previous backup.")
            
            if st.button("📦 Create Backup"):
                backup_path = generate_backup()
                if backup_path:
                    with open(backup_path, "rb") as file:
                        st.download_button(
                            label="📥 Download Backup File",
                            data=file,
                            file_name=backup_path,
                            mime="application/octet-stream"
                        )
                    st.success(f"Backup created: {backup_path}")
                else:
                    st.error("Database file not found.")

    elif st.session_state.page == "Recurring":
        st.subheader("🔄 Recurring Expenses & Subscriptions")
        st.write("Manage your recurring subscriptions and bills.")
        
        with st.expander("➕ Add Recurring Expense", expanded=True):
            with st.form("recurring_form", clear_on_submit=True):
                r_desc = st.text_input("Description", placeholder="e.g. Netflix")
                r_amt = st.number_input("Amount", min_value=0.0)
                r_cat = st.selectbox("Category", ["Utilities", "Entertainment", "Rent", "Other"], key="rec_cat")
                r_freq = st.selectbox("Frequency", ["Monthly", "Weekly", "Yearly"])
                r_date = st.date_input("Next Due Date")
                
                if st.form_submit_button("Add Recurring"):
                    add_recurring_expense_db(user_id, r_amt, r_cat, r_desc, r_freq, r_date.strftime("%Y-%m-%d"))
                    st.success("Recurring expense added!")
                    st.rerun()
        
        if recurring:
            st.write("#### Active Subscriptions")
            for r in recurring:
                col_r1, col_r2, col_r3, col_r4 = st.columns([2, 1, 1, 1])
                with col_r1:
                        st.write(f"**{get_category_icon(r['category'])} {r['description']}** ({r['frequency']})")
                col_r2.write(f"₹{r['amount']}")
                col_r3.write(f"Due: {r['next_due_date']}")
                
                # Delete Confirmation
                if col_r4.button("🗑️", key=f"del_{r['id']}"):
                    st.session_state[f"confirm_del_{r['id']}"] = True
                    st.rerun()
                    
                if st.session_state.get(f"confirm_del_{r['id']}"):
                    st.warning("Delete this?")
                    if st.button("✅ Yes", key=f"yes_{r['id']}"):
                        delete_recurring_expense_db(r['id'])
                        del st.session_state[f"confirm_del_{r['id']}"]
                        st.rerun()
                    if st.button("❌ No", key=f"no_{r['id']}"):
                        del st.session_state[f"confirm_del_{r['id']}"]
                        st.rerun()
        else:
            st.info("No recurring expenses set.")

    elif st.session_state.page == "Investments":
        st.subheader("🚀 Investments & SIPs")
        st.write("Track your investments and SIPs.")
        
        with st.expander("➕ Add New Investment / SIP", expanded=True):
            with st.form("investment_form", clear_on_submit=True):
                i_name = st.text_input("Name", placeholder="e.g. Nifty 50 Index Fund")
                i_amt = st.number_input("Amount (₹)", min_value=0.0)
                i_type = st.selectbox("Type", ["SIP", "Lumpsum", "Stock", "Gold", "FD", "Other"])
                i_freq = st.selectbox("Frequency", ["Monthly", "One-time", "Weekly", "Yearly"])
                i_date = st.date_input("Start Date/Investment Date")
                
                if st.form_submit_button("Add Investment"):
                    add_investment_db(user_id, i_name, i_amt, i_type, i_date.strftime("%Y-%m-%d"), i_freq)
                    st.success("Investment added!")
                    st.rerun()
        
        # --- Market Indices ---
        st.markdown("### 📈 Market Overview")
        try:
            import yfinance as yf
            
            @st.cache_data(ttl=3600*12) # Cache for 12 hours
            def get_market_data(ticker, period="1mo", interval="1d"):
                try:
                    t = yf.Ticker(ticker)
                    hist = t.history(period=period, interval=interval)
                    return hist['Close'] if not hist.empty else None
                except:
                    return None

            col_idx1, col_idx2 = st.columns(2)
            
            with col_idx1:
                st.write("**Nifty 50**")
                nifty = get_market_data("^NSEI")
                if nifty is not None:
                    st.line_chart(nifty, height=200)
                else:
                    st.error("Failed to load Nifty 50 data.")
            
            with col_idx2:
                st.write("**BSE Sensex**")
                sensex = get_market_data("^BSESN")
                if sensex is not None:
                    st.line_chart(sensex, height=200)
                else:
                    st.error("Failed to load Sensex data.")
                    
        except ImportError:
            st.warning("⚠️ `yfinance` library not found. Please install it to view market data.")
        except Exception as e:
            st.error(f"Error loading market data: {e}")
            
        st.divider()

        if investments:
            st.write("#### Your Portfolio")
            
            # Summary Metrics
            total_invested = sum(i['amount'] for i in investments)
            monthly_sip = sum(i['amount'] for i in investments if i['type'] == 'SIP' and i['frequency'] == 'Monthly')
            
            m1, m2 = st.columns(2)
            m1.metric("Total Invested Value ( tracked )", f"₹{total_invested:,.2f}")
            m2.metric("Monthly SIP Amount", f"₹{monthly_sip:,.2f}")
            
            st.divider()
            
            for inv in investments:
                with st.container():
                    col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns([2, 1, 1, 1, 0.5])
                    with col_i1:
                        st.write(f"**{inv['name']}**")
                        st.caption(f"{inv['type']} • {inv['frequency']}")
                    col_i2.write(f"₹{inv['amount']:,.2f}")
                    col_i3.write(f"{inv['start_date']}")
                    
                    # Delete
                    if col_i5.button("🗑️", key=f"del_inv_{inv['id']}"):
                        delete_investment_db(inv['id'])
                        st.rerun()
                    st.divider()
        else:
            st.info("No investments tracked yet. Start your journey! 🚀")

    elif st.session_state.page == "Settings":
        st.subheader("⚙️ Settings")
        st.write("Configure your account details.")
        col1, col2 = st.columns([1, 2])
        with col1:
                new_initial = st.number_input("Initial Balance (₹)", value=float(initial_balance), min_value=0.0, step=100.0)
                
                if st.button("Update Balance", type="primary"):
                    set_initial_balance_db(user_id, new_initial)
                    st.success(f"Initial balance updated to ₹{new_initial:,.2f}")
                    time.sleep(1)
                    st.rerun()

    elif st.session_state.page == "Previous":
        st.subheader("🗓️ Archived Month Expenses")
        st.write("View expenses from previous months that have been reset.")
        
        archived = get_archived_expenses(user_id)
        
        if archived:
            df_arch = pd.DataFrame(archived)
            
            # Formatting
            df_arch['display_category'] = df_arch['category'].apply(lambda x: f"{get_category_icon(x)} {x}")
            
            # Extract Month from archived_at to group better
            df_arch['archived_at'] = pd.to_datetime(df_arch['archived_at'])
            df_arch['Archived Date'] = df_arch['archived_at'].dt.strftime("%d %b %Y, %H:%M")
            
            st.dataframe(
                df_arch[['Archived Date', 'date', 'display_category', 'description', 'amount', 'type']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No archived data found.")

if __name__ == "__main__":
    main()

