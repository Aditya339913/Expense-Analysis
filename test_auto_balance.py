
import sqlite3
from database import (
    init_db, create_user, authenticate_user, 
    add_expense_batch_db, get_expenses_db, set_initial_balance_db, get_initial_balance_db,
    undo_last_reset
)

DB_FILE = "bank.db"

def test_auto_balance_logic():
    print("--- Testing Auto-Match Balance Logic ---")
    
    # 1. Setup Test User
    test_user = "test_balance_user"
    if not authenticate_user(test_user, "password"):
        create_user(test_user, "password")
    
    user_id = authenticate_user(test_user, "password")
    
    # Reset State
    set_initial_balance_db(user_id, 0.0)
    # Clear expenses (manually for test speed)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    print("Initial State: Balance=0, Expenses=0")
    
    # 2. Simulate logic that happens in main.py
    # Batch: 1 Expense of 5000
    batch = [(user_id, 5000.0, "Shopping", "Laptop", "2025-01-01", "expense")]
    
    # Logic Copy-Paste from main.py (simulated)
    import_income = sum(x[1] for x in batch if x[5] == 'income')
    import_expense = sum(x[1] for x in batch if x[5] == 'expense')
    net_import_change = import_income - import_expense
    
    current_initial = get_initial_balance_db(user_id)
    # Current net is 0
    projected_balance = current_initial + net_import_change # 0 - 5000 = -5000
    
    print(f"Projected Balance: {projected_balance}")
    
    if projected_balance < 0:
        needed = abs(projected_balance)
        new_initial = current_initial + needed
        print(f"Adjusting Initial Balance by +{needed}")
        set_initial_balance_db(user_id, new_initial)
        
    add_expense_batch_db(batch)
    
    # 3. Verify
    final_initial = get_initial_balance_db(user_id)
    print(f"Final Initial Balance: {final_initial}")
    
    assert final_initial == 5000.0
    
    # Verify final dashboard balance would be 0 (5000 initial - 5000 expense)
    # Re-calc net worth logic
    txs = get_expenses_db(user_id)
    total_spent = sum(e['amount'] for e in txs if e['type'] == 'expense')
    final_net_worth = final_initial - total_spent
    print(f"Final Net Worth: {final_net_worth}")
    
    assert final_net_worth == 0.0
    
    print("✅ Auto-Balance Logic Verified!")

if __name__ == "__main__":
    init_db()
    test_auto_balance_logic()
