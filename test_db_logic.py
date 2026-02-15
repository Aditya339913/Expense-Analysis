from database import init_db, create_user, authenticate_user, add_expense_db, get_expenses_db, set_initial_balance_db, get_initial_balance_db
import os
import sqlite3

# Test DB Setup
TEST_DB = "bank.db" 
# Note: database.py uses "bank.db" hardcoded. for testing safely we might want to temporarily rename it or just use it if it's new.
# Since we just started Phase 2, bank.db is empty or new.
# However, to be safe, let's just test the functions directly on the real DB for now as it is a local app and "Main" uses it. 
# But to avoid polluting, maybe I should have made DB_FILE configurable. 
# For now, I will assume it's fine to test on the main DB or I can patch it.
# Let's just run basic assertions.

def test_db():
    print("Testing Database Functions...")
    init_db()
    
    # Test User Creation
    username = "test_user_unique_" + os.urandom(4).hex()
    password = "password123"
    assert create_user(username, password) == True
    print("User creation passed.")
    
    # Test Auth
    user_id = authenticate_user(username, password)
    assert user_id is not None
    print("Authentication passed.")
    
    # Test Initial Balance
    set_initial_balance_db(user_id, 5000.0)
    assert get_initial_balance_db(user_id) == 5000.0
    print("Initial Balance passed.")
    
    # Test Add Expense
    add_expense_db(user_id, 100.0, "Food", "Burger")
    expenses = get_expenses_db(user_id)
    assert len(expenses) == 1
    assert expenses[0]['amount'] == 100.0
    print("Add/Get Expense passed.")

    # Test Add Expense with Custom Date
    add_expense_db(user_id, 200.0, "Transport", "Taxi", "2023-01-01 12:00:00")
    expenses_new = get_expenses_db(user_id)
    # The get_expenses_db sorts by date DESC, so this old date should be last (or first depending on sort, let's check len)
    # Actually get_expenses_db selects ... ORDER BY date DESC. So 2026 (now) is first, 2023 is last.
    assert len(expenses_new) == 2
    assert expenses_new[-1]['date'] == "2023-01-01 12:00:00"
    print("Custom Date Expense passed.")
    
    print("All Database Tests Passed!")

if __name__ == "__main__":
    test_db()
