import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def detect_anomalies(expenses):
    """
    Detects expenses that are significantly higher than the average for their category.
    Rule: Expense > 3 * Median of Category.
    Returns a list of alerts (strings).
    """
    if not expenses:
        return []

    df = pd.DataFrame(expenses)
    alerts = []

    # Calculate Median per category
    category_stats = df.groupby('category')['amount'].median().reset_index()
    category_stats.rename(columns={'amount': 'median'}, inplace=True)
    
    # Iterate over recent expenses (last 5)
    # Ensure date is datetime for sorting
    if 'date' in df.columns and df['date'].dtype == 'object':
        try:
            df['date'] = pd.to_datetime(df['date'], format='mixed')
        except:
            df['date'] = pd.to_datetime(df['date']) # Fallback
        
    recent = df.sort_values('date', ascending=False).head(5)
    
    for _, row in recent.iterrows():
        cat = row['category']
        amt = row['amount']
        
        median = category_stats[category_stats['category'] == cat]['median'].values[0]
        
        # Threshold: 3 * Median. Minimum threshold 100 to avoid noise.
        threshold = max(3 * median, 100)
        
        if amt > threshold:
            alerts.append(f"⚠️ Unusual Spend: ₹{amt:,.2f} on {cat} ({row['description']}) is unusually high (Median: ₹{median:,.0f}).")

    return list(set(alerts)) # Deduplicate

def predict_month_end(expenses, current_balance):
    """
    Predicts total spending by month-end and estimated savings.
    """
    if not expenses:
        return 0.0, 0.0

    df = pd.DataFrame(expenses)
    df['date'] = pd.to_datetime(df['date'])
    
    current_month = datetime.now().strftime('%Y-%m')
    df_month = df[df['date'].dt.to_period('M').astype(str) == current_month]
    
    spent_so_far = df_month['amount'].sum()
    
    today = datetime.now().day
    days_in_month = (datetime.now().replace(day=1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)).day
    
    if today == 0: return spent_so_far, current_balance # Should not happen
    
    # Linear Projection
    estimated_total = (spent_so_far / today) * days_in_month
    
    # Estimated Savings (This is tricky without Income context, assume Initial Balance was "Budget" or "Income")
    # If Initial Balance is treated as "Total Available for Month":
    estimated_savings = max(0, current_balance - (estimated_total - spent_so_far))
    
    return estimated_total, estimated_savings

def generate_savings_tips(expenses):
    """
    Generates personalized tips based on spending habits.
    """
    if not expenses:
        return ["Start adding expenses to get personalized tips!"]
        
    df = pd.DataFrame(expenses)
    top_cat = df.groupby('category')['amount'].sum().idxmax()
    
    tips = []
    tips.append(f"💡 You spend the most on **{top_cat}**. Try to set a budget for this category.")
    
    # Check frequency
    if len(df) > 20:
        freq_cat = df['category'].mode()[0]
        tips.append(f"💡 You make frequent purchases in **{freq_cat}**. Buying in bulk might save money.")
        
    return tips

def check_recurring_reminders(recurring_expenses):
    """
    Checks if any recurring expense is due soon (within 3 days).
    """
    alerts = []
    today = datetime.now().date()
    
    for item in recurring_expenses:
        try:
            due_date = datetime.strptime(item['next_due_date'], "%Y-%m-%d").date()
            days_left = (due_date - today).days
            
            if 0 <= days_left <= 3:
                alerts.append(f"📅 Reminder: **{item['description']}** ({item['category']}) of ₹{item['amount']} is due in {days_left} days!")
            elif days_left < 0:
                alerts.append(f"❗ Overdue: **{item['description']}** was due on {item['next_due_date']}.")
        except:
            continue
            
    return alerts
