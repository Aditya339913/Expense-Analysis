
import yfinance as yf

def test_yfinance():
    print("--- Testing yfinance ---")
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d")
        if not hist.empty:
            print(f"Successfully fetched Nifty 50 data. Rows: {len(hist)}")
            print(hist.tail())
        else:
            print("Fetched empty data for Nifty 50.")
            
        sensex = yf.Ticker("^BSESN")
        hist_s = sensex.history(period="5d")
        if not hist_s.empty:
            print(f"Successfully fetched Sensex data. Rows: {len(hist_s)}")
        else:
            print("Fetched empty data for Sensex.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_yfinance()
