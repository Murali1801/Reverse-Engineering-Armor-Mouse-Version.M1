import sys
import os
import json
import time
import win32gui
import win32api
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QMessageBox, QListWidget, QListWidgetItem, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import ctypes

# Enable DPI awareness to ensure coordinates match screen pixels
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
except:
    ctypes.windll.user32.SetProcessDPIAware()

# Comprehensive list of buttons and controls to calibrate
CALIBRATION_TARGETS = [
    # --- Top Navigation ---
    ("NAV_KEYS", "Top Nav: Keys"),
    ("NAV_PERF", "Top Nav: Performance"),
    ("NAV_LIGHT", "Top Nav: Light"),
    ("NAV_MACRO", "Top Nav: Macro"),
    ("NAV_GUN", "Top Nav: Gun"),
    
    # --- Sidebar & Bottom ---
    ("PROFILE_SEL", "Sidebar: Profile Select"),
    ("PROFILE_ADD", "Sidebar: Profile Add (+)"),
    ("PROFILE_DEL", "Sidebar: Profile Delete (-)"),
    ("PROFILE_MENU", "Sidebar: Profile Menu (...)"),
    ("PROFILE_RENAME", "Sidebar: Rename Profile Input"),
    ("RESET", "Bottom: Reset Button"),
    ("APPLY", "Bottom: Apply Button"),
    
    # --- Keys Page ---
    ("KEY_BTN_1", "Keys: Left Click"),
    ("KEY_BTN_2", "Keys: Right Click"),
    ("KEY_BTN_3", "Keys: Middle Button"),
    ("KEY_BTN_4", "Keys: Forward"),
    ("KEY_BTN_5", "Keys: Backward"),

    # --- Key Assignment Dropdown ---
    ("ASSIGN_BASIC", "Assign: Basic Function"),
    # --- Basic Function Sub-menu ---
    ("BASIC_LEFT", "Basic: Left Click"),
    ("BASIC_RIGHT", "Basic: Right Click"),
    ("BASIC_MIDDLE", "Basic: Middle Button"),
    ("BASIC_FORWARD", "Basic: Forward"),
    ("BASIC_BACKWARD", "Basic: Backward"),
    ("BASIC_SCROLL_UP", "Basic: Scroll Up"),
    ("BASIC_SCROLL_DOWN", "Basic: Scroll Down"),

    ("ASSIGN_HIGH_ORDER", "Assign: High Order Function"),
    # --- High Order Function Sub-menu ---
    ("HIGH_ORDER_DOUBLE", "High Order: Double Click"),
    ("HIGH_ORDER_THREE", "High Order: Three Click"),
    ("HIGH_ORDER_LIGHT", "High Order: Light Mode Switch"),
    ("HIGH_ORDER_SNIPER", "High Order: Sniper Key"),

    ("ASSIGN_OFF", "Assign: Button Off"),
    ("ASSIGN_SHORTCUT", "Assign: Shortcut"),
    ("ASSIGN_MACRO", "Assign: Select A Macro"),
    ("ASSIGN_DPI", "Assign: DPI"),
    # --- DPI Sub-menu ---
    ("DPI_CYCLE", "DPI: DPI Cycle"),
    ("DPI_PLUS", "DPI: DPI +"),
    ("DPI_MINUS", "DPI: DPI -"),

    ("ASSIGN_REPORT", "Assign: Report"),
    # --- Report Sub-menu ---
    ("REPORT_CYCLE", "Report: Report Cycle"),
    ("REPORT_PLUS", "Report: Report +"),
    ("REPORT_MINUS", "Report: Report -"),

    ("ASSIGN_MEDIA", "Assign: Multimedia"),
    # --- Multimedia Sub-menu ---
    ("MEDIA_PLAYER", "Media: Media Player"),
    ("MEDIA_PLAY_PAUSE", "Media: Play / Pause"),
    ("MEDIA_STOP", "Media: Stop"),
    ("MEDIA_PREV", "Media: Previous Track"),
    ("MEDIA_NEXT", "Media: Next Track"),
    ("MEDIA_VOL_PLUS", "Media: Volume +"),
    ("MEDIA_VOL_MINUS", "Media: Volume -"),
    ("MEDIA_MUTE", "Media: Mute"),

    ("ASSIGN_WINDOWS", "Assign: Windows"),
    # --- Windows Sub-menu ---
    ("WIN_HOME", "Windows: Browser Home"),
    ("WIN_FAV", "Windows: Browser Favorites"),
    ("WIN_FWD", "Windows: Browser Forward"),
    ("WIN_BACK", "Windows: Browser Backward"),
    ("WIN_STOP", "Windows: Browser Stop"),
    ("WIN_REFRESH", "Windows: Browser Refresh"),
    ("WIN_SEARCH", "Windows: Browser Search"),
    ("WIN_EMAIL", "Windows: Email"),
    ("WIN_CALC", "Windows: Calculator"),
    ("WIN_MY_PC", "Windows: My Computer"),

    ("ASSIGN_OFFICE", "Assign: Office"),
    # --- Office Sub-menu ---
    ("OFFICE_CUT", "Office: Cut"),
    ("OFFICE_COPY", "Office: Copy"),
    ("OFFICE_PASTE", "Office: Paste"),
    ("OFFICE_OPEN", "Office: Open"),
    ("OFFICE_SAVE", "Office: Save"),
    ("OFFICE_FIND", "Office: Find"),
    ("OFFICE_REDO", "Office: Redo"),
    ("OFFICE_SELECT_ALL", "Office: Select All"),
    ("OFFICE_NEW", "Office: New"),
    ("OFFICE_PRINT", "Office: Print"),
    
    ("ASSIGN_ADVANCE", "Assign: Advance Function"),
    # --- Advance Function Sub-menu ---
    ("ADV_SWAP", "Advance: Swap Windows"),
    ("ADV_CLOSE", "Advance: Close Window"),
    ("ADV_DESKTOP", "Advance: Show Desktop"),
    ("ADV_LOCK", "Advance: Lock PC"),
    ("ADV_RUN", "Advance: Run Command"),
    
    # --- Performance Page ---
    ("PERF_DPI_COMBO", "Perf: Max DPI Combo"),
    ("PERF_DPI_SLD_1", "Perf: DPI Level 1 Slider"),
    ("PERF_POLLING_1", "Perf: Polling 125Hz"),
    ("PERF_POLLING_4", "Perf: Polling 1000Hz"),
    ("PERF_MOVE_SLD", "Perf: Mouse Move Speed Slider"),
    ("PERF_SCROLL_SLD", "Perf: Scroll Speed Slider"),
    ("PERF_DBLCLICK_SLD", "Perf: Double Click Slider"),
    
    # --- Light Page ---
    ("LIGHT_MODE_1", "Light: Effect Mode 1"),
    ("LIGHT_BRIGHT_SLD", "Light: Brightness Slider"),
    ("LIGHT_FIX_COLOR", "Light: Fix Color Button"),
    
    # --- Macro Page ---
    ("MACRO_FLD_ADD", "Macro: Add Folder"),
    ("MACRO_RECORD", "Macro: Start Record"),
    
    # --- Reset Popup ---
    ("POPUP_OK", "Popup: OK Button"),
    ("POPUP_CANCEL", "Popup: Cancel Button"),
    ("POPUP_CLOSE", "Popup: Close (X) Button"),

    # --- Profile Menu Dropdown ---
    ("MENU_IMPORT", "Profile Menu: Import Profile"),
    ("MENU_EXPORT", "Profile Menu: Export Profile"),
]

class Calibrator(QWidget):
    def __init__(self):
        super().__init__()
        self.target_window_title = "Armor Version.M1"
        self.output_file = "button_map.json"
        self.mappings = {}
        
        # Load existing mappings
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r') as f:
                    self.mappings = json.load(f)
            except: pass

        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Armor Exhaustive Calibrator")
        self.setGeometry(100, 100, 500, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # Header
        lbl_head = QLabel("Select an item below and press 'F8' to calibrate.")
        lbl_head.setStyleSheet("font-size: 14px; font-weight: bold; color: #00B0FF; padding: 10px;")
        lbl_head.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_head)
        
        # Status
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #666; font-style: italic;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { font-size: 14px; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #00B0FF; color: white; }
        """)
        self.populate_list()
        layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save to JSON")
        btn_save.setHeight = 40
        btn_save.setStyleSheet("font-weight: bold; padding: 10px;")
        btn_save.clicked.connect(self.save_map)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # F8 Timer listener
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_hotkey)
        self.timer.start(100) # Check every 100ms
        
    def populate_list(self):
        self.list_widget.clear()
        for key, name in CALIBRATION_TARGETS:
            item_text = f"{name}"
            # Check if already mapped
            if key in self.mappings:
                coords = self.mappings[key]
                item_text = f"✅ {name}  ➡  {coords}"
            else:
                item_text = f"❌ {name}"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, key) # Store the ID
            self.list_widget.addItem(item)
            
    def check_hotkey(self):
        # Check for F8 press
        if win32api.GetAsyncKeyState(0x77) & 0x8000: 
            self.capture_position()
            time.sleep(0.3) # Debounce
            
    def capture_position(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            self.lbl_status.setText("Please select an item from the list first!")
            return
            
        key = current_item.data(Qt.UserRole)
        
        hwnd = win32gui.FindWindow(None, self.target_window_title)
        if not hwnd:
            self.lbl_status.setText(f"❌ Window '{self.target_window_title}' not found!")
            return
            
        # Get point in screen coordinates
        cursor_x, cursor_y = win32api.GetCursorPos()
        
        # Convert screen coordinates to CLIENT coordinates
        client_point = win32gui.ScreenToClient(hwnd, (cursor_x, cursor_y))
        rel_x, rel_y = client_point[0], client_point[1]
        
        # Save mapping
        self.mappings[key] = (rel_x, rel_y)
        
        # Update UI text
        # Find the original name from our list
        original_name = next((name for k, name in CALIBRATION_TARGETS if k == key), key)
        current_item.setText(f"✅ {original_name}  ➡  ({rel_x}, {rel_y})")
        
        self.lbl_status.setText(f"Captured {key}: ({rel_x}, {rel_y})")
        
        # Auto-select next item for convenience
        next_row = self.list_widget.currentRow() + 1
        if next_row < self.list_widget.count():
            self.list_widget.setCurrentRow(next_row)

    def save_map(self):
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.mappings, f, indent=4)
            QMessageBox.information(self, "Success", f"Saved {len(self.mappings)} buttons to {self.output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Calibrator()
    ex.show()
    sys.exit(app.exec_())
