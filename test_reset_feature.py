
import sqlite3
import os
from database import (
    init_db, create_user, authenticate_user, 
    add_expense_db, get_expenses_db, set_initial_balance_db, get_initial_balance_db,
    archive_and_reset_expenses, get_archived_expenses
)

DB_FILE = "bank.db"

def test_reset_functionality():
    print("--- Testing Reset Functionality ---")
    
    # 1. Setup Test User
    test_user = "test_reset_user"
    if not authenticate_user(test_user, "password"):
        create_user(test_user, "password")
    
    user_id = authenticate_user(test_user, "password")
    print(f"User ID: {user_id}")
    
    # 2. Add Data
    print("Adding expenses and balance...")
    set_initial_balance_db(user_id, 5000.0)
    add_expense_db(user_id, 100.0, "Food", "Burger", transaction_type="expense")
    add_expense_db(user_id, 2000.0, "Salary", "Work", transaction_type="income")
    
    # Verify Data Exists
    expenses = get_expenses_db(user_id)
    balance = get_initial_balance_db(user_id)
    print(f"Current Expenses Count: {len(expenses)}")
    print(f"Current Balance: {balance}")
    
    assert len(expenses) >= 2
    assert balance == 5000.0
    
    # 3. Perform Reset
    print("Executing Reset...")
    archive_and_reset_expenses(user_id)
    
    # 4. Verify Reset
    print("Verifying Reset...")
    new_expenses = get_expenses_db(user_id)
    new_balance = get_initial_balance_db(user_id)
    
    print(f"New Expenses Count: {len(new_expenses)}")
    print(f"New Balance: {new_balance}")
    
    assert len(new_expenses) == 0
    assert new_balance == 0.0
    
    # 5. Verify Archive
    print("Verifying Archive...")
    archived = get_archived_expenses(user_id)
    print(f"Archived Count: {len(archived)}")
    
    # Check if our added expenses are in archive
    found_burger = False
    found_salary = False
    
    for item in archived:
        if item['description'] == "Burger" and item['amount'] == 100.0:
            found_burger = True
        if item['description'] == "Work" and item['amount'] == 2000.0:
            found_salary = True
            
    assert found_burger
    assert found_salary
    
    print("✅ All Tests Passed!")

if __name__ == "__main__":
    init_db() # Ensure DB is valid
    test_reset_functionality()
