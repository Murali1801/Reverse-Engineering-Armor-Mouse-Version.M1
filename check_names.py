# check_names.py
import sys
import win32gui
from pywinauto import Application

# 1. Connect
hwnd = win32gui.FindWindow(None, "Armor Version.M1")
if not hwnd:
    print("❌ Armor window not found!")
    sys.exit()

print(f"✅ Connected to Window: {hwnd}")
app = Application(backend="uia").connect(handle=hwnd)
win = app.window(handle=hwnd)

# 2. Dump visible controls
print("\n🔍 DUMPING VISIBLE CONTROLS (Look for 'Name' or 'Title'):")
print("="*60)
try:
    # This prints a tree of every button Python can click
    win.print_control_identifiers(depth=3) 
except Exception as e:
    print(f"Error dumping tree: {e}")
print("="*60)