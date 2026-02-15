
import sqlite3
import os
from database import (
    init_db, create_user, authenticate_user, 
    add_expense_db, get_expenses_db, set_initial_balance_db, get_initial_balance_db,
    archive_and_reset_expenses, get_archived_expenses, undo_last_reset
)

DB_FILE = "bank.db"

def test_undo_functionality():
    print("--- Testing Undo Functionality ---")
    
    # 1. Setup Test User
    test_user = "test_undo_user"
    if not authenticate_user(test_user, "password"):
        create_user(test_user, "password")
    
    user_id = authenticate_user(test_user, "password")
    print(f"User ID: {user_id}")
    
    # Clean slate for test user
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM archived_expenses WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM archived_balances WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # 2. Add Data
    print("Adding expenses and balance...")
    set_initial_balance_db(user_id, 10000.0)
    add_expense_db(user_id, 500.0, "Entertainment", "Movie", transaction_type="expense")
    
    # 3. Perform Reset
    print("Executing Reset...")
    archive_and_reset_expenses(user_id)
    
    # Verify Reset
    assert get_initial_balance_db(user_id) == 0.0
    assert len(get_expenses_db(user_id)) == 0
    print("Reset Confirmed.")
    
    # 4. Perform Undo
    print("Executing Undo...")
    success = undo_last_reset(user_id)
    assert success == True
    
    # 5. Verify Undo
    print("Verifying Data Restored...")
    restored_balance = get_initial_balance_db(user_id)
    restored_expenses = get_expenses_db(user_id)
    
    print(f"Restored Balance: {restored_balance}")
    print(f"Restored Expenses Count: {len(restored_expenses)}")
    
    assert restored_balance == 10000.0
    assert len(restored_expenses) == 1
    assert restored_expenses[0]['description'] == "Movie"
    
    # 6. Verify Archive Cleared
    archived = get_archived_expenses(user_id)
    print(f"Archived Count (Should be 0): {len(archived)}")
    assert len(archived) == 0
    
    print("✅ All Tests Passed!")

if __name__ == "__main__":
    init_db()
    test_undo_functionality()
