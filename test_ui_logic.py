from ui_utils import get_category_icon, get_custom_css

def test_ui():
    print("Testing UI Utils...")
    
    # 1. Test Icons
    assert get_category_icon("Food") == "🍔"
    assert get_category_icon("Unknown") == "💸"
    print("Icons Verified.")
    
    # 2. Test CSS Generation
    dark_css = get_custom_css("Dark")
    assert "#0E1117" in dark_css
    
    light_css = get_custom_css("Light")
    assert "#F8F9FA" in light_css
    print("CSS Generation Verified.")
    
    print("UI Utils Passed!")

if __name__ == "__main__":
    test_ui()
