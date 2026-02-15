from ai_logic import detect_anomalies, predict_month_end, generate_savings_tips, check_recurring_reminders
from datetime import datetime, timedelta

def test_ai():
    print("Testing AI Logic...")
    
    # 1. Test Anomaly Detection
    expenses = [
        {'amount': 100, 'category': 'Food', 'description': 'Burger', 'date': '2023-01-01 12:00:00'},
        {'amount': 120, 'category': 'Food', 'description': 'Pizza', 'date': '2023-01-02 12:00:00'},
        {'amount': 110, 'category': 'Food', 'description': 'Pasta', 'date': '2023-01-03 12:00:00'},
        {'amount': 5000, 'category': 'Food', 'description': 'Gold Steak', 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    ]
    # Mean ~110, Std ~10. Threshold ~130. 5000 should be anomaly.
    anomalies = detect_anomalies(expenses)
    assert len(anomalies) > 0
    print(f"Anomaly Detected: {anomalies[0]}")
    
    # 2. Test Prediction
    # 10 days in, spent 1000. Month end should be ~3000.
    # We need to mock "today" inside the function or just accept the logic uses real date.
    # Since function uses datetime.now(), we can only check if it returns a float > 0.
    pred_total, pred_savings = predict_month_end(expenses, 5000)
    assert pred_total > 0
    print(f"Prediction: {pred_total:.2f}")
    
    # 3. Test Recurring Reminders
    today = datetime.now().strftime("%Y-%m-%d")
    recurring = [
        {'description': 'Netflix', 'category': 'Ent', 'amount': 200, 'next_due_date': today}
    ]
    reminders = check_recurring_reminders(recurring)
    assert len(reminders) == 1
    print(f"Reminder: {reminders[0]}")
    
    print("AI Logic Verification Passed!")

if __name__ == "__main__":
    test_ai()
