import sqlite3
import bcrypt
import os
from datetime import datetime

DB_FILE = "bank.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        currency TEXT DEFAULT '₹',
        initial_balance REAL DEFAULT 0.0,
        created_at TEXT,
        family_id TEXT
    )''')
    
    # Expenses Table (Renaming concept to Transactions internally or just adding type)
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT,
        transaction_type TEXT DEFAULT 'expense',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # ... (Rest of tables) ...

    conn.commit()
    conn.close()
    
    # Run Migration to ensure existing DBs get new columns
    migrate_db()

def migrate_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check expenses table for transaction_type
    c.execute("PRAGMA table_info(expenses)")
    cols = [info[1] for info in c.fetchall()]
    if 'transaction_type' not in cols:
        print("Migrating: Adding transaction_type to expenses...")
        c.execute("ALTER TABLE expenses ADD COLUMN transaction_type TEXT DEFAULT 'expense'")
        
    # Check users table for family_id
    c.execute("PRAGMA table_info(users)")
    cols = [info[1] for info in c.fetchall()]
    if 'family_id' not in cols:
        print("Migrating: Adding family_id to users...")
        c.execute("ALTER TABLE users ADD COLUMN family_id TEXT")
        
    # Ensure archived_expenses table exists
    c.execute('''CREATE TABLE IF NOT EXISTS archived_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT,
        transaction_type TEXT,
        archived_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Ensure archived_balances table exists
    c.execute('''CREATE TABLE IF NOT EXISTS archived_balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        balance REAL,
        archived_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
        
    conn.commit()
    conn.close()

# --- User Auth Functions ---

def create_user(username, password, family_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password_hash, created_at, family_id) VALUES (?, ?, ?, ?)", 
                  (username, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), family_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        # user[1] should be bytes if stored as BLOB, or needs encoding if TEXT
        stored_hash = user[1]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return user[0] # Return user_id
    return None

def create_session(user_id):
    import uuid
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Ensure table exists (lazy init for migration)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute("INSERT INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)", 
              (session_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return session_id

def validate_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if table exists first
    try:
        c.execute("SELECT s.user_id, u.username FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.session_id = ?", (session_id,))
        res = c.fetchone()
        conn.close()
        if res:
            return res[0], res[1] # user_id, username
    except sqlite3.OperationalError:
        conn.close()
    return None, None

def delete_session(session_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    except:
        pass
    conn.close()


# --- Expense Functions ---

def add_expense_db(user_id, amount, category, description, date=None, transaction_type='expense'):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO expenses (user_id, amount, category, description, date, transaction_type) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, amount, category, description, date, transaction_type))
    conn.commit()
    conn.close()

def add_expense_batch_db(expenses_list):
    """
    Batch insert expenses/income. 
    expenses_list: list of tuples (user_id, amount, category, description, date, transaction_type)
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executemany("INSERT INTO expenses (user_id, amount, category, description, date, transaction_type) VALUES (?, ?, ?, ?, ?, ?)",
                  expenses_list)
    conn.commit()
    conn.close()

def get_expenses_db(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT amount, category, description, date, id, transaction_type FROM expenses WHERE user_id = ? ORDER BY date DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    expenses = []
    for r in rows:
        expenses.append({
            "amount": r[0],
            "category": r[1],
            "description": r[2],
            "date": r[3],
            "id": r[4],
            "type": r[5] if r[5] else 'expense'
        })
    return expenses

def update_expense_db(expense_id, amount, category, description, transaction_type='expense'):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE expenses SET amount=?, category=?, description=?, transaction_type=? WHERE id=?", 
              (amount, category, description, transaction_type, expense_id))
    conn.commit()
    conn.close()

def delete_expense_db(expense_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()

def set_initial_balance_db(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET initial_balance = ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    
def get_initial_balance_db(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT initial_balance FROM users WHERE id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] is not None else 0.0

def archive_and_reset_expenses(user_id):
    """
    Moves all current expenses for the user to the archive table and resets the initial balance to 0.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Get current expenses
    c.execute("SELECT amount, category, description, date, transaction_type FROM expenses WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    
    # 2. Get current initial balance
    c.execute("SELECT initial_balance FROM users WHERE id = ?", (user_id,))
    res = c.fetchone()
    current_balance = res[0] if res else 0.0
    
    archived_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. Archive Balance
    c.execute("INSERT INTO archived_balances (user_id, balance, archived_at) VALUES (?, ?, ?)", 
              (user_id, current_balance, archived_at))
    
    if rows:
        # 4. Archive expenses
        archived_data = [(user_id, r[0], r[1], r[2], r[3], r[4], archived_at) for r in rows]
        c.executemany("INSERT INTO archived_expenses (user_id, amount, category, description, date, transaction_type, archived_at) VALUES (?, ?, ?, ?, ?, ?, ?)", archived_data)
        
        # 5. Delete from main expenses table
        c.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
    
    # 6. Reset Initial Balance
    c.execute("UPDATE users SET initial_balance = 0 WHERE id = ?", (user_id,))
    
    conn.commit()
    conn.close()

def undo_last_reset(user_id):
    """
    Undoes the last reset action by restoring expenses and balance from the archive.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Find last archive timestamp
    c.execute("SELECT archived_at FROM archived_balances WHERE user_id = ? ORDER BY archived_at DESC LIMIT 1", (user_id,))
    res = c.fetchone()
    
    if not res:
        conn.close()
        return False # No archives found
        
    last_archived_at = res[0]
    
    # 2. Restore Balance
    c.execute("SELECT balance FROM archived_balances WHERE user_id = ? AND archived_at = ?", (user_id, last_archived_at))
    bal_res = c.fetchone()
    if bal_res:
        restored_balance = bal_res[0]
        c.execute("UPDATE users SET initial_balance = ? WHERE id = ?", (restored_balance, user_id))
        
    # 3. Restore Expenses
    c.execute("SELECT amount, category, description, date, transaction_type FROM archived_expenses WHERE user_id = ? AND archived_at = ?", (user_id, last_archived_at))
    archived_rows = c.fetchall()
    
    if archived_rows:
        restored_data = [(user_id, r[0], r[1], r[2], r[3], r[4]) for r in archived_rows]
        c.executemany("INSERT INTO expenses (user_id, amount, category, description, date, transaction_type) VALUES (?, ?, ?, ?, ?, ?)", restored_data)
        
    # 4. Clean up Archive
    c.execute("DELETE FROM archived_balances WHERE user_id = ? AND archived_at = ?", (user_id, last_archived_at))
    c.execute("DELETE FROM archived_expenses WHERE user_id = ? AND archived_at = ?", (user_id, last_archived_at))
    
    conn.commit()
    conn.close()
    return True

def get_archived_expenses(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT amount, category, description, date, transaction_type, archived_at FROM archived_expenses WHERE user_id = ? ORDER BY archived_at DESC, date DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    archived = []
    for r in rows:
        archived.append({
            "amount": r[0],
            "category": r[1],
            "description": r[2],
            "date": r[3],
            "type": r[4],
            "archived_at": r[5]
        })
    return archived

# --- Recurring Expense Functions ---

def add_recurring_expense_db(user_id, amount, category, description, frequency, next_due_date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Ensure recurring_expenses table exists
    c.execute('''CREATE TABLE IF NOT EXISTS recurring_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        frequency TEXT,
        next_due_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute("INSERT INTO recurring_expenses (user_id, amount, category, description, frequency, next_due_date) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, amount, category, description, frequency, next_due_date))
    conn.commit()
    conn.close()

def get_recurring_expenses_db(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Ensure recurring_expenses table exists
    c.execute('''CREATE TABLE IF NOT EXISTS recurring_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        frequency TEXT,
        next_due_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute("SELECT id, amount, category, description, frequency, next_due_date FROM recurring_expenses WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    recurring = []
    for r in rows:
        recurring.append({
            "id": r[0],
            "amount": r[1],
            "category": r[2],
            "description": r[3],
            "frequency": r[4],
            "next_due_date": r[5]
        })
    return recurring

def delete_recurring_expense_db(rec_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM recurring_expenses WHERE id=?", (rec_id,))
    conn.commit()
    conn.close()

# --- Investment Functions ---

def add_investment_db(user_id, name, amount, type, start_date, frequency):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        amount REAL,
        type TEXT,
        start_date TEXT,
        frequency TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute("INSERT INTO investments (user_id, name, amount, type, start_date, frequency) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, name, amount, type, start_date, frequency))
    conn.commit()
    conn.close()

def get_investments_db(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        amount REAL,
        type TEXT,
        start_date TEXT,
        frequency TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute("SELECT id, name, amount, type, start_date, frequency FROM investments WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    investments = []
    for r in rows:
        investments.append({
            "id": r[0],
            "name": r[1],
            "amount": r[2],
            "type": r[3],
            "start_date": r[4],
            "frequency": r[5]
        })
    return investments

def delete_investment_db(inv_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM investments WHERE id=?", (inv_id,))
    conn.commit()
    conn.close()

