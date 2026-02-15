import pandas as pd
from ui_utils import parse_bank_statement, auto_categorize, generate_backup
from database import init_db, add_expense_batch_db, get_expenses_db

def test_financial_suite():
    print("Testing Financial Suite...")
    
    # 1. Test CSV Parsing
    print("\n--- Testing CSV Parsing ---")
    df = parse_bank_statement("sample_statement.csv")
    if df is not None:
        print("Success: CSV Parsed")
        print(df.head())
        
        # 2. Test Auto Categorization & Batch Insert logic
        print("\n--- Testing Auto Categorization ---")
        batch = []
        user_id = 999 
        for _, row in df.iterrows():
            desc = str(row.get('description', ''))
            cat = auto_categorize(desc)
            print(f"'{desc}' -> {cat}")
            
            # Type logic check
            tx_type = 'expense'
            if 'type' in row:
                t = str(row['type']).lower()
                if 'credit' in t: tx_type = 'income'
            print(f"Type: {tx_type}")

    # 3. Test Backup
    print("\n--- Testing Backup ---")
    backup = generate_backup()
    if backup:
        print(f"Backup created: {backup}")
    else:
        print("Backup failed (DB might not exist yet if init_db not called in this context)")

if __name__ == "__main__":
    init_db() # Ensure DB exists
    test_financial_suite()
