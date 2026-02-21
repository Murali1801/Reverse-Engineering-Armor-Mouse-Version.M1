# armor_api.py
import win32gui
import time
from pywinauto import mouse, keyboard

class ArmorAPI:
    def __init__(self):
        self.title = "Armor Version.M1"

    def get_window_pos(self):
        """Finds the current absolute position of the CLIENT area (content) on screen."""
        hwnd = win32gui.FindWindow(None, self.title)
        if not hwnd:
            return None
        # ClientToScreen with (0,0) gives the screen position of the content area's top-left
        point = win32gui.ClientToScreen(hwnd, (0, 0))
        return point

    def click_at(self, offset_coords):
        """Calculates Absolute Position = Window_Pos + Offset and performs a click."""
        win_pos = self.get_window_pos()
        if not win_pos:
            print(f"❌ Window '{self.title}' not found!")
            return

        abs_x = win_pos[0] + offset_coords[0]
        abs_y = win_pos[1] + offset_coords[1]

        try:
            # Performs the click at the absolute screen coordinate
            mouse.click(button='left', coords=(abs_x, abs_y))
            print(f"✅ Clicked Absolute: ({abs_x}, {abs_y})")
        except Exception as e:
            print(f"❌ Click failed: {e}")

    def rename_profile(self, new_name):
        """Clicks the rename field, clears it, and types the new name."""
        coords = COMMANDS.get("PROFILE_RENAME")
        if not coords:
            print("❌ PROFILE_RENAME coordinates not found!")
            return

        self.click_at(coords)
        time.sleep(0.2) # Wait for focus
        
        # Select All (Ctrl+A) and Delete to clear existing text
        # Using SendKeys syntax
        try:
            keyboard.SendKeys('^a') # Select All
            time.sleep(0.1)
            keyboard.SendKeys('{DELETE}') # Clear
            time.sleep(0.1)
            
            # Type new name. Escape special chars if needed, but for now raw string.
            # pywinauto SendKeys handles most chars, but specialized ones need braces.
            # Assuming simple alphanumeric for profile names.
            keyboard.SendKeys(new_name, with_spaces=True)
            time.sleep(0.1)
            
            # Confirm
            keyboard.SendKeys('{ENTER}')
            time.sleep(0.1)
            
            # User specified click to save/unfocus
            # Coordinates: (455, 351)
            self.click_at((455, 351))
            
            print(f"✅ Renamed profile to: {new_name}")
        except Exception as e:
            print(f"❌ Rename failed: {e}")

    def connect(self):
        """Checks if the window exists."""
        return self.get_window_pos() is not None

# ==========================================
# 📍 VERIFIED CALIBRATED COORDINATE MAPPING
# Based on ScreenToClient Calibration
# ==========================================
COMMANDS = {
    # Navigation
    "NAV_KEYS":        (570, 62),
    "NAV_PERF":        (920, 62),
    "NAV_MACRO":       (1277, 60),
    
    # Sidebar
    "PROFILE_SEL":     (400, 190),
    "PROFILE_ADD":     (108, 243),
    "PROFILE_DEL":     (235, 245),
    "PROFILE_MENU":    (366, 242),
    "PROFILE_RENAME":  (236, 355), # Added
    "RESET":           (237, 428),
    "APPLY":           (237, 632),

    # Shared Warning Popup (Reset / Delete Profile)
    "POPUP_OK":        (725, 607),
    "POPUP_CANCEL":    (872, 606),
    "POPUP_CLOSE":     (1055, 311),

    
    # Profile Menu Dropdown
    "MENU_IMPORT":     (366, 285),
    "MENU_EXPORT":     (362, 315),

    # Key Assignment Buttons
    "KEY_BTN_1":       (1275, 187),
    "KEY_BTN_2":       (1277, 307),
    "KEY_BTN_3":       (1278, 426),
    "KEY_BTN_4":       (1277, 548),
    "KEY_BTN_5":       (1282, 667),

    # Key Assignment Dropdown Menu
    "ASSIGN_BASIC":    (1276, 231),
    "ASSIGN_HIGH_ORDER": (1271, 262),
    "ASSIGN_OFF":      (1272, 295),
    "ASSIGN_SHORTCUT": (1276, 325),
    "ASSIGN_MACRO":    (1273, 355),
    "ASSIGN_DPI":      (1276, 387),
    "ASSIGN_REPORT":   (1268, 422),
    "ASSIGN_MEDIA":    (1266, 447),
    "ASSIGN_WINDOWS":  (1268, 477),
    "ASSIGN_OFFICE":   (1270, 512),
    "ASSIGN_ADVANCE":  (1270, 543),

    # Basic Function Sub-menu
    "BASIC_LEFT":      (1468, 232),
    "BASIC_RIGHT":     (1471, 265),
    "BASIC_MIDDLE":    (1477, 297),
    "BASIC_FORWARD":   (1483, 327),
    "BASIC_BACKWARD":  (1483, 366),
    "BASIC_SCROLL_UP": (1486, 391),
    "BASIC_SCROLL_DOWN": (1485, 425),

    # High Order Function Sub-menu
    "HIGH_ORDER_DOUBLE": (1486, 266),
    "HIGH_ORDER_THREE":  (1491, 296),
    "HIGH_ORDER_LIGHT":  (1496, 327),
    "HIGH_ORDER_SNIPER": (1493, 361),

    # DPI Sub-menu
    "DPI_CYCLE":       (1480, 393),
    "DPI_PLUS":        (1483, 421),
    "DPI_MINUS":       (1478, 457),

    # Report Sub-menu
    "REPORT_CYCLE":    (1477, 420),
    "REPORT_PLUS":     (1478, 450),
    "REPORT_MINUS":    (1483, 486),

    # Multimedia Sub-menu
    "MEDIA_PLAYER":     (1478, 447),
    "MEDIA_PLAY_PAUSE": (1475, 480),
    "MEDIA_STOP":       (1477, 517),
    "MEDIA_PREV":       (1478, 546),
    "MEDIA_NEXT":       (1478, 575),
    "MEDIA_VOL_PLUS":   (1483, 610),
    "MEDIA_VOL_MINUS":  (1485, 636),
    "MEDIA_MUTE":       (1488, 670),

    # Windows Sub-menu
    "WIN_HOME":        (1495, 483),
    "WIN_FAV":         (1498, 511),
    "WIN_FWD":         (1500, 545),
    "WIN_BACK":        (1503, 576),
    "WIN_STOP":        (1503, 616),
    "WIN_REFRESH":     (1498, 641),
    "WIN_SEARCH":      (1500, 671),
    "WIN_EMAIL":       (1500, 705),
    "WIN_CALC":        (1502, 735),
    "WIN_MY_PC":       (1505, 765)
}