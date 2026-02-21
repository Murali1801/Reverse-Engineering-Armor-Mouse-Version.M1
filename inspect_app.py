# inspect_app.py
import sys
from pywinauto import Application

# The exact title as it appears on the window
TARGET_TITLE = "Armor Version.M1"

def inspect_ui():
    print(f"Searching for '{TARGET_TITLE}'...")
    
    try:
        # Try to connect. backend="uia" is required for DuiLib/WPF apps.
        app = Application(backend="uia").connect(title=TARGET_TITLE, timeout=10)
        main_window = app.window(title=TARGET_TITLE)
        
        if main_window.exists():
            print("\n✅ CONNECTION SUCCESSFUL!")
            print("dumping UI structure... (this may take 10 seconds)")
            print("-" * 60)
            
            # This prints every button the tool can see
            main_window.print_control_identifiers(depth=2)
            
            print("-" * 60)
            print("\n👉 LOOK ABOVE: Do you see names like 'Apply', 'Button', or 'Ok'?")
            print("   YES -> Copy the 'title' or 'auto_id' for the next script.")
            print("   NO  -> The UI is 'Blind'. We must use the XML-Fallback method.")
        else:
            print("❌ Window found in process list, but not visible on screen.")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("Tip: Make sure the Armor app is OPEN and run this script as ADMIN.")

if __name__ == "__main__":
    inspect_ui()