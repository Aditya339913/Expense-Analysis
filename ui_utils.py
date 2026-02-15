import streamlit as st

def get_category_icon(category):
    icons = {
        "Food": "🍔",
        "Transport": "🚗",
        "Utilities": "💡",
        "Entertainment": "🎬",
        "Shopping": "🛍️",
        "Health": "🏥",
        "Education": "📚",
        "Rent": "🏠",
        "Other": "📝"
    }
    return icons.get(category, "💸")

def get_custom_css(theme="Dark"):
    # Animations
    animations = """
<style>
@keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
}
.stMetric, .stDataFrame, .stPlotlyChart {
    animation: fadeIn 0.5s ease-out;
}
</style>
"""
    
    if theme == "Dark":
        base_css = """
<style>
/* Dark Theme */
.stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Salina', sans-serif; }
.stMetric {
    background-color: #1E2130 !important;
    color: #ffffff !important;
    border: 1px solid #2E3440;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
}
[data-testid="stMetricLabel"] { color: #A0AEC0 !important; }
[data-testid="stMetricValue"] { color: #E2E8F0 !important; }
div.stButton > button {
    background-color: #1E2130;
    color: white;
    border: 1px solid #4A5568;
    padding: 15px 20px;
    font-size: 16px;
    border-radius: 10px;
    transition: all 0.3s ease;
    font-weight: 600;
}
div.stButton > button:hover {
    background-color: #4C51BF;
    border-color: #4C51BF;
    transform: translateY(-2px);
    box-shadow: 0px 5px 15px rgba(76, 81, 191, 0.4);
}
h1, h2, h3, h4, h5, h6 { color: #E2E8F0 !important; font-family: 'Salina', sans-serif; }
</style>
"""
    else: # Light Theme
        base_css = """
<style>
/* Light Theme */
.stApp { background-color: #F8F9FA; color: #212529; font-family: 'Salina', sans-serif; }
.stMetric {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #E9ECEF;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
}
[data-testid="stMetricLabel"] { color: #6C757D !important; }
[data-testid="stMetricValue"] { color: #212529 !important; }
div.stButton > button {
    background-color: #FFFFFF;
    color: #495057;
    border: 1px solid #CED4DA;
    padding: 15px 20px;
    font-size: 16px;
    border-radius: 10px;
    transition: all 0.3s ease;
    font-weight: 600;
}
div.stButton > button:hover {
    background-color: #4C51BF;
    color: white;
    border-color: #4C51BF;
    transform: translateY(-2px);
    box-shadow: 0px 5px 15px rgba(76, 81, 191, 0.2);
}
h1, h2, h3, h4, h5, h6 { color: #212529 !important; font-family: 'Salina', sans-serif; }
/* Fix Table Text Color in Light Mode */
[data-testid="stDataFrame"] { color: #212529 !important; }
</style>
"""
        
    return base_css + animations

import shutil
import os
from datetime import datetime
import pandas as pd

def generate_backup():
    """
    Creates a backup of the current database.
    Returns the path to the backup file.
    """
    db_file = "bank.db"
    if not os.path.exists(db_file):
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_bank_{timestamp}.db"
    shutil.copy(db_file, backup_file)
    return backup_file

def auto_categorize(description):
    """
    Simple keyword matching for auto-categorization.
    """
    desc = description.lower()
    mapping = {
        "Food": ["burger", "pizza", "swiggy", "zomato", "restaurant", "cafe", "coffee", "grocery", "mart"],
        "Transport": ["uber", "ola", "fuel", "petrol", "parking", "train", "bus", "flight", "taxi"],
        "Utilities": ["electricity", "water", "bill", "recharge", "mobile", "broadband", "gas"],
        "Entertainment": ["netflix", "prime", "movie", "cinema", "spotify", "game", "steam"],
        "Shopping": ["amazon", "flipkart", "myntra", "nike", "adidas", "clothes", "mall"],
        "Health": ["pharmacy", "doctor", "hospital", "med", "clinic"],
        "Salary": ["salary", "credit", "interest", "refund", "dividend", "bonus"]
    }
    
    for category, keywords in mapping.items():
        for keyword in keywords:
            if keyword in desc:
                return category
    return "Other"

def parse_bank_statement(uploaded_file):
    """
    Parses an uploaded CSV file. 
    Attempts to unify column names to: Date, Description, Amount, Type (optional).
    Returns a DataFrame or None.
    """
    try:
        df = pd.read_csv(uploaded_file)
        
        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Mapping attempts
        col_map = {}
        for col in df.columns:
            if "date" in col: col_map["date"] = col
            elif "desc" in col or "particulars" in col or "narration" in col: col_map["description"] = col
            elif "amount" in col or "debit" in col or "credit" in col: col_map["amount"] = col
            elif "type" in col or "cr/dr" in col: col_map["type"] = col

        if "date" in col_map and "amount" in col_map:
            # Rename for consistency
            rename_dict = {v: k for k, v in col_map.items()}
            df = df.rename(columns=rename_dict)
            
            # Ensure description exists
            if "description" not in df.columns:
                df["description"] = "Imported Transaction"
                
            return df
        else:
            return None # Could not identify mandatory columns
            
    except Exception as e:
        return None
