from main import BankManager
import os
import json

TEST_DB = "test_expenses.json"

# Setup
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# Test Initialization
manager = BankManager(TEST_DB)
assert manager.get_balance() == 0.0
assert manager.get_initial_balance() == 0.0

# Test Set Initial Balance
manager.set_initial_balance(1000.0)
assert manager.get_initial_balance() == 1000.0
assert manager.get_balance() == 1000.0

# Test Add Expense
manager.add_expense(100.0, "Food", "Lunch")
assert manager.get_balance() == 900.0
assert len(manager.get_history()) == 1
assert manager.get_total_spent() == 100.0

# Test Persistence
manager2 = BankManager(TEST_DB)
assert manager2.get_balance() == 900.0
assert len(manager2.get_history()) == 1

print("All backend logic tests passed!")

# Cleanup
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
