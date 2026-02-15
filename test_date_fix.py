
from datetime import datetime

def test_date_parsing():
    print("--- Testing Date Parsing Logic ---")
    
    # Mock Data with mixed formats
    expense_data = [
        {'date': '2025-12-28 12:00:00'}, # Standard
        {'date': '2025-12-29'},          # AI Generated / CSV Import often just date
        {'date': 'invalid-date'}         # Garbage
    ]
    
    dates = []
    for e in expense_data:
        try:
            # Try full format first
            d = datetime.strptime(e['date'], "%Y-%m-%d %H:%M:%S").date()
            print(f"Parsed Full: {d}")
        except ValueError:
            try:
                # Fallback to just date
                d = datetime.strptime(e['date'], "%Y-%m-%d").date()
                print(f"Parsed Short: {d}")
            except ValueError:
                # Fallback to today
                d = datetime.now().date()
                print(f"Fallback to Today: {d}")
        dates.append(d)
        
    assert len(dates) == 3
    assert dates[0].year == 2025
    assert dates[1].year == 2025
    assert dates[2] == datetime.now().date()
    
    print("✅ Date Parsing Verification Successful!")

if __name__ == "__main__":
    test_date_parsing()
