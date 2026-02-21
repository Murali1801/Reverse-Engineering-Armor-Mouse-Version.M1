# calibrate.py
import win32gui
import win32api
import time
import math

def get_relative_coords():
    print("---------------------------------------------------------")
    print("🛠️  CALIBRATION MODE")
    print("---------------------------------------------------------")
    print("1. Hover your mouse over a button in the Armor App.")
    print("2. RIGHT-CLICK to capture the coordinate.")
    print("3. Press 'Ctrl + C' in this terminal to stop.")
    print("---------------------------------------------------------")

    hwnd = win32gui.FindWindow(None, "Armor Version.M1")
    if not hwnd:
        print("❌ Error: Armor App not found! Open it first.")
        return

    rect = win32gui.GetWindowRect(hwnd)
    x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
    print(f"✅ Hooked Window at: {x},{y} ({w}x{h})")

    last_click = 0

    while True:
        # Check for Right Click (Key Code 0x02)
        if win32api.GetKeyState(0x02) < 0:
            current_time = time.time()
            if current_time - last_click > 0.5: # Debounce
                mx, my = win32api.GetCursorPos()
                
                # Calculate Relative Position
                rel_x = mx - x
                rel_y = my - y
                
                # Verify click is inside window
                if 0 <= rel_x <= w and 0 <= rel_y <= h:
                    print(f'    "YOUR_BUTTON_NAME": ({rel_x}, {rel_y}),')
                else:
                    print("⚠️ Clicked outside the window!")
                
                last_click = current_time
        time.sleep(0.01)

if __name__ == "__main__":
    get_relative_coords()