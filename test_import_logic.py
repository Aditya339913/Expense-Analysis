
import pandas as pd
from datetime import datetime

# Mock the logic from main.py (since main.py is inside a function and hard to import partially without refactoring)
def mock_import_logic(row):
    desc = str(row.get('description', '')).lower()
    cat = "Other" # simplified
    
    # Determine Type
    amt = float(row.get('amount', 0))
    
    # Default Logic
    if amt > 0:
        tx_type = 'income' if cat == 'Salary' else 'expense'
    else:
        tx_type = 'expense'
        amt = abs(amt) 
    
    # Keyword override for Income
    income_keywords = ['salary', 'credit', 'interest', 'refund', 'dividend', 'deposit']
    if any(k in desc for k in income_keywords):
        tx_type = 'income'
        amt = abs(amt)

    if 'type' in row and pd.notna(row['type']):
        t = str(row['type']).lower()
        if 'credit' in t or 'cr' in t or 'income' in t: tx_type = 'income'
        elif 'debit' in t or 'dr' in t or 'expense' in t: tx_type = 'expense'
        
    return tx_type, amt

def test_import_logic():
    print("--- Testing Import Logic ---")
    
    test_cases = [
        # description, amount, type_col, expected_type, expected_amt
        ("Burger", -500, None, "expense", 500.0),      # Standard negative expense
        ("Salary", 50000, None, "income", 50000.0),    # Keyword match +ve
        ("Deposit", 1000, None, "income", 1000.0),     # Keyword match +ve
        ("Refund", -200, None, "income", 200.0),       # Keyword match override negative (refund is income)
        ("Unknown", 100, None, "expense", 100.0),      # Default positive unknown -> expense (safer assumption?)
        ("Grocery", 200, "Debit", "expense", 200.0),   # Explicit Type
        ("Freelance", 5000, "Credit", "income", 5000.0)# Explicit Type
    ]
    
    for desc, amt, t_col, exp_type, exp_amt in test_cases:
        row = {'description': desc, 'amount': amt}
        if t_col: row['type'] = t_col
        
        res_type, res_amt = mock_import_logic(row)
        
        print(f"Input: {desc}, {amt}, {t_col} -> Got: {res_type}, {res_amt}")
        
        assert res_type == exp_type, f"Failed type for {desc}"
        assert res_amt == exp_amt, f"Failed amt for {desc}"
        
    print("✅ All Import Logic Tests Passed!")

if __name__ == "__main__":
    test_import_logic()
