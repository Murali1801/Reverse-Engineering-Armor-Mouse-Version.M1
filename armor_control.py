# armor_control.py
from pywinauto import Application
import time

class ArmorController:
    def __init__(self, title="Armor Version.M1"):
        self.title = title
        self.app = None
        self.window = None

    def connect(self):
        try:
            self.app = Application(backend="uia").connect(title=self.title)
            self.window = self.app.window(title=self.title)
            return True
        except:
            return False

    def click_smart(self, button_id, fallback_x=0, fallback_y=0):
        """
        Attempts to click by Name. If impossible, clicks by Relative Coordinate.
        """
        if not self.connect():
            print("❌ Error: App not running.")
            return

        try:
            # METHOD A: The Professional Way (By Name)
            # We search for a button matching the ID
            btn = self.window.child_window(title=button_id, control_type="Button")
            
            if btn.exists():
                print(f"✅ Found button '{button_id}'. Clicking via Automation...")
                btn.invoke() # Tries to click programmatically
                return

        except Exception as e:
            print(f"⚠️ 'Smart Click' failed: {e}")

        # METHOD B: The "Relative" Fallback (DuiLib Safe Mode)
        # If we can't find the button object, we click the coordinates relative to the window.
        # This works even if the window is moved!
        print(f"⚠️ Button '{button_id}' hidden. Using Relative Click ({fallback_x}, {fallback_y})...")
        try:
            self.window.click_input(coords=(fallback_x, fallback_y))
        except Exception as e:
            print(f"❌ Critical Fail: {e}")

# ==========================================
# ⚙️ CONFIGURATION ZONE
# ==========================================
# If Step 1 showed names, put them here.
# If Step 1 showed NOTHING, put "None" and fill in the X/Y coords.
# The X/Y coords are RELATIVE to the window (Top-Left is 0,0).
BUTTON_MAP = {
    "APPLY": {
        "id": "Apply",       # Try to find button named "Apply"
        "x": 404, "y": 500   # Fallback: 404px Right, 500px Down
    },
    "DPI": {
        "id": "DPI Switch",  
        "x": 120, "y": 80
    },
    "MACRO": {
        "id": "Macro",
        "x": 300, "y": 300
    }
}