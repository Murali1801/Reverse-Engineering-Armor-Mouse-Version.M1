import sys
import os
import time

# 🛑 CRITICAL: COM initialization for thread safety
sys.coinit_flags = 2 

from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFrame, QStackedWidget, 
                             QComboBox, QLineEdit, QGraphicsDropShadowEffect, QGridLayout, QSpacerItem, QSizePolicy, QMenu, QMainWindow)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QEvent, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QPixmap, QFont, QIcon

import subprocess
import win32gui
import win32api
import win32con

# ==========================================
# 📍 VERIFIED CALIBRATED COORDINATE MAPPING
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
    "PROFILE_RENAME":  (236, 355),
    "RESET":           (237, 428),
    "APPLY":           (237, 632),

    # Shared Warning Popup
    "POPUP_OK":        (725, 607),
    "POPUP_CANCEL":    (872, 606),
    "POPUP_CLOSE":     (1055, 311),

    # Key Assignment Buttons
    "KEY_BTN_1":       (1275, 187),
    "KEY_BTN_2":       (1277, 307),
    "KEY_BTN_3":       (1278, 426),
    "KEY_BTN_4":       (1277, 548),
    "KEY_BTN_5":       (1282, 667),

    # Menus (These coordinates might need verification if they are sub-window relative)
    # Assuming they are relative to main window client area for now based on previous API.
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

    "BASIC_LEFT":      (1468, 232),
    "BASIC_RIGHT":     (1471, 265),
    "BASIC_MIDDLE":    (1477, 297),
    "BASIC_FORWARD":   (1483, 327),
    "BASIC_BACKWARD":  (1483, 366),
    "BASIC_SCROLL_UP": (1486, 391),
    "BASIC_SCROLL_DOWN": (1485, 425),

    # High Order (Aliased for overlay1.py compatibility)
    "HO_DOUBLE":       (1486, 266), # HIGH_ORDER_DOUBLE
    "HO_SNIPER":       (1493, 361), # HIGH_ORDER_SNIPER

    # Media (Aliased)
    "MEDIA_PP":        (1475, 480), # MEDIA_PLAY_PAUSE
    "MEDIA_V+":        (1483, 610), # VOL_PLUS
    "MEDIA_V-":        (1485, 636), # VOL_MINUS

    # Windows (Aliased)
    "WIN_WEB":         (1495, 483), # WIN_HOME
    "WIN_CALC":        (1502, 735),
    "WIN_MY_PC":       (1505, 765),
}

class ArmorAPI:
    def __init__(self):
        self.title = "Armor Version.M1"
        self.hwnd = None

    def connect(self):
        """Finds the window, launching it if necessary, and HIDES it."""
        self.hwnd = win32gui.FindWindow(None, self.title)
        
        if not self.hwnd:
            print("🚀 Launching MouseDriver.exe...")
            if os.path.exists("MouseDriver.exe"):
                subprocess.Popen("MouseDriver.exe")
                # Wait for window to appear
                for _ in range(50): # 5 seconds max
                    self.hwnd = win32gui.FindWindow(None, self.title)
                    if self.hwnd: break
                    time.sleep(0.1)
            else:
                print("❌ MouseDriver.exe not found!")
                return

        if self.hwnd:
            # Hide the window
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            # Ensure it doesn't show up in taskbar (GWL_EXSTYLE could be modified if needed, but Hide is usually enough)
            print(f"✅ Connected to '{self.title}' (Hidden)")
        else:
            print("❌ Failed to connect to application.")

    def click_at(self, coords):
        """Sends a background click to the specific client coordinates."""
        if not self.hwnd: self.connect()
        if not self.hwnd: return

        x, y = coords
        lparam = win32api.MAKELONG(x, y)
        
        # PostMessage allows sending without waiting for processing, keeping our UI responsive
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        time.sleep(0.05) # Brief hold
        win32api.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        print(f"📡 Sent Background Click: ({x}, {y})")

    def rename_profile(self, new_name):
        """Attempts to rename by sending clicks and keystrokes to the background window."""
        if not self.hwnd: return
        
        coords = COMMANDS.get("PROFILE_RENAME")
        if not coords: return

        self.click_at(coords)
        time.sleep(0.2)
        
        # Send Ctrl+A (Select All)
        # Note: Input simulation to background windows is tricky. 
        # We try sending WM_KEYDOWN messages.
        
        def send_key(vk_code):
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.02)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, vk_code, 0)

        # Select All (Ctrl + A)
        # For simplicity in background, we might just try Backspacing a lot or 
        # just sending chars if the field auto-clears. 
        # Standard Ctrl+A via messages:
        # It's unreliable to send combo keys via PostMessage to inactive windows.
        # Fallback: Just try to type the new name. If it appends, user can clear manually first in our UI.
        
        # Clear field (Backspace x 20)
        for _ in range(20): send_key(win32con.VK_BACK)
        
        # Type new name
        for char in new_name:
            # Get virtual key code
            res = win32api.VkKeyScan(char)
            vk_code = res & 0xFF
            send_key(vk_code)
            
        # Enter to confirm
        send_key(win32con.VK_RETURN)
        
        # Click away to save
        self.click_at((455, 351)) # Random spot to deselect

# ==========================================
# 🎨 MODERN THEME CONFIGURATION (#FC832C, #8BBAD8, #FFFFFF)
# ==========================================
STYLESHEET = """
/* Global Reset & Font */
QWidget { 
    font-family: 'Poppins', 'Segoe UI', sans-serif; 
    font-size: 15px; 
    color: #2D3436; 
    outline: none;
}

/* Main Window Background */
QWidget#CentralWidget {
    background-color: #FDFDFD; /* Slightly off-white to let pure white cards pop */
}

/* --- Typography --- */
QLabel#LogoTitle { 
    color: #2D3436; 
    font-size: 52px; 
    font-weight: 800; 
    letter-spacing: -1px;
    background: transparent;
}

QLabel#SectionLabel { 
    font-size: 13px; 
    font-weight: 600;
    color: #8BBAD8; /* Secondary Blue for labels */
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
}

/* --- Card Containers --- */
QFrame#Card {
    background-color: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #EFF0F1;
}

/* --- Navigation --- */
QPushButton#NavBtn { 
    background: transparent; 
    border: none; 
    color: #B2BEC3; 
    font-size: 18px; 
    font-weight: 600;
    min-height: 40px;
    margin: 0 15px;
}
QPushButton#NavBtn:hover {
    color: #FC832C; /* Orange Hover */
}
QPushButton#NavBtn:checked { 
    color: #FC832C; /* Orange Active */
    border-bottom: 3px solid #FC832C; 
}

/* --- Inputs (Modern Flat Style) --- */
QComboBox, QLineEdit { 
    background-color: #F9FAFB;
    border: 1px solid #DFE6E9;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
    color: #2D3436;
    selection-background-color: #FC832C;
}
QComboBox:hover, QLineEdit:hover {
    border-color: #8BBAD8; /* Blue hover */
    background-color: #FFFFFF;
}
QComboBox:focus, QLineEdit:focus {
    border: 1px solid #FC832C; /* Orange focus */
    background-color: #FFFFFF;
}
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow { 
    image: none; 
    border-left: 5px solid transparent; 
    border-right: 5px solid transparent; 
    border-top: 6px solid #636E72; 
    margin-right: 10px;
}

/* --- Action Buttons (Left Panel) --- */
QPushButton#IconBtn {
    background-color: #FFFFFF;
    border: 1px solid #DFE6E9;
    border-radius: 8px;
    color: #636E72;
    font-size: 18px;
    font-weight: bold;
    min-width: 45px;
    min-height: 40px;
}
QPushButton#IconBtn:hover {
    background-color: #FFF0E0; /* Light Orange Tint */
    color: #FC832C;
    border-color: #FC832C;
}
QPushButton#IconBtn:pressed {
    background-color: #FFE0B2;
}

/* --- Primary & Secondary Buttons --- */
QPushButton#PrimaryBtn {
    background-color: #FC832C; /* Orange Primary */
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 15px;
    padding: 12px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #E67622;
    margin-top: -1px; 
}
QPushButton#PrimaryBtn:pressed {
    background-color: #D35400;
    margin-top: 0px;
}

QPushButton#SecondaryBtn {
    background-color: transparent;
    color: #636E72;
    border: 1px solid #DFE6E9;
    border-radius: 10px;
    font-weight: 600;
    font-size: 15px;
    padding: 12px;
}
QPushButton#SecondaryBtn:hover {
    border-color: #8BBAD8; /* Blue Border */
    color: #8BBAD8;
    background-color: #FFFFFF;
}

/* --- Key Binding Buttons (Right Panel) --- */
QPushButton#KeyBtn { 
    background-color: #FFFFFF; 
    border: 1px solid #EFF0F1;
    border-left: 4px solid #8BBAD8; /* Light Blue Accent Line initially */
    border-radius: 8px;
    color: #2D3436; 
    padding: 15px 20px; 
    text-align: left;
    font-size: 15px; 
    font-weight: 500;
}
QPushButton#KeyBtn:hover { 
    background-color: #FFFFFF;
    border: 1px solid #FC832C;
    border-left: 6px solid #FC832C; /* Orange Accent on Hover */
    color: #FC832C;
}

/* --- Window Controls --- */
QPushButton#WinBtn {
    background: transparent;
    border: none;
    color: #B2BEC3;
    font-size: 16px;
    border-radius: 15px;
    min-width: 30px;
    min-height: 30px;
}
QPushButton#WinBtn:hover { background-color: #DFE6E9; color: #2D3436; }
QPushButton#WinBtn#CloseBtn:hover { background-color: #FF7675; color: white; }

/* --- Menus --- */
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #DFE6E9;
    border-radius: 8px;
    padding: 5px;
}
QMenu::item {
    padding: 8px 25px;
    border-radius: 4px;
    color: #2D3436;
}
QMenu::item:selected {
    background-color: #FFF0E0; /* Light Orange */
    color: #FC832C;
}

/* --- Popup --- */
QFrame#PopupContainer {
    background-color: #FFFFFF;
    border: 1px solid #DFE6E9;
    border-radius: 16px;
}
QLabel#PopupTitle { color: #FC832C; font-size: 20px; font-weight: bold; }
QLabel#PopupMessage { color: #2D3436; font-size: 16px; }
"""

class Worker(QThread):
    def __init__(self):
        super().__init__()
        self.queue = []
        self.running = True
        self.api = ArmorAPI()
    def run(self):
        self.api.connect()
        while self.running:
            if self.queue:
                task = self.queue.pop(0)
                if isinstance(task, str):
                    coords = COMMANDS.get(task)
                    if coords: self.api.click_at(coords)
                elif isinstance(task, tuple) and len(task) == 2:
                    if task[0] == "RENAME":
                        self.api.rename_profile(task[1])
                    else:
                        self.api.click_at(task)
            time.sleep(0.1)
    def add_task(self, task): self.queue.append(task)
    def stop(self): self.running = False


class ConfirmationPopup(QFrame):
    accepted = pyqtSignal()
    
    def __init__(self, parent, title_text, message_text):
        super().__init__(parent)
        self.setObjectName("PopupContainer")
        self.setFixedSize(500, 280) # Smaller, cleaner popup
        
        # Add Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
        
        self.move(parent.width() // 2 - 250, parent.height() // 2 - 140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 30)
        
        # Header
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("PopupTitle")
        layout.addWidget(lbl_title)
        
        layout.addSpacing(15)
        
        # Message
        lbl_msg = QLabel(message_text)
        lbl_msg.setObjectName("PopupMessage")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)
        
        layout.addStretch(1)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        btn_row.addStretch(1)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.setFixedSize(100, 40)
        btn_cancel.clicked.connect(self.hide)
        
        btn_ok = QPushButton("Confirm")
        btn_ok.setObjectName("PrimaryBtn")
        btn_ok.setFixedSize(120, 40)
        btn_ok.clicked.connect(self.on_ok)
        
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def on_ok(self):
        self.accepted.emit()
        self.hide()


class ArmorDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = Worker()
        self.worker.start()
        self.base_img_path = "res/skins/mouse/"
        self.default_mouse = "mouse.png"
        self.assignments = {
            "KEY_BTN_1": "BASIC_LEFT",
            "KEY_BTN_2": "BASIC_RIGHT",
            "KEY_BTN_3": "BASIC_MIDDLE",
            "KEY_BTN_4": "BASIC_FORWARD",
            "KEY_BTN_5": "BASIC_BACKWARD"
        }
        self.initUI()
        self.oldPos = self.pos()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(1600, 935)
        self.setStyleSheet(STYLESHEET)
            
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(20)

        # === HEADER (Logo + Nav + Window Controls) ===
        header_layout = QHBoxLayout()
        
        # 1. Logo
        lbl_logo = QLabel("armor"); lbl_logo.setObjectName("LogoTitle")
        header_layout.addWidget(lbl_logo)
        
        header_layout.addStretch(1)

        # 2. Navigation
        nav_container = QHBoxLayout()
        nav_container.setSpacing(10)
        nav_container.addWidget(self.create_nav_btn("Keys", 0))
        nav_container.addWidget(self.create_nav_btn("Performance", 1))
        nav_container.addWidget(self.create_nav_btn("Macro", 2))
        header_layout.addLayout(nav_container)
        
        header_layout.addStretch(1)

        # 3. Window Controls
        win_controls = QHBoxLayout()
        win_controls.setSpacing(8)
        btn_min = QPushButton("─"); btn_min.setObjectName("WinBtn"); btn_min.clicked.connect(self.showMinimized)
        btn_close = QPushButton("✕"); btn_close.setObjectName("WinBtn"); btn_close.setObjectName("CloseBtn"); btn_close.clicked.connect(self.close)
        win_controls.addWidget(btn_min)
        win_controls.addWidget(btn_close)
        header_layout.addLayout(win_controls)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # === MAIN CONTENT (Stacked) ===
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # -- PAGE 0: KEYS --
        page_keys = QWidget()
        
        grid_keys = QGridLayout(page_keys)
        grid_keys.setContentsMargins(0, 0, 0, 0)
        grid_keys.setSpacing(40)
        grid_keys.setColumnStretch(0, 25) # Left (Profile)
        grid_keys.setColumnStretch(1, 45) # Center (Mouse)
        grid_keys.setColumnStretch(2, 30) # Right (Keys)

        # --- LEFT PANEL (Profile Card) ---
        left_card = QFrame(); left_card.setObjectName("Card")
        # Add shadow to card
        shadow_left = QGraphicsDropShadowEffect(); shadow_left.setBlurRadius(20); shadow_left.setColor(QColor(0,0,0,15)); shadow_left.setOffset(0, 5)
        left_card.setGraphicsEffect(shadow_left)
        
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(25, 30, 25, 30)
        left_layout.setSpacing(15)
        
        lbl_s = QLabel("Select Profile"); lbl_s.setObjectName("SectionLabel")
        left_layout.addWidget(lbl_s)
        
        self.cb_profile = QComboBox(); self.cb_profile.addItems(["Profile 1", "Default", "Game Mode"])
        left_layout.addWidget(self.cb_profile)
        
        # Tools Row
        row_tools = QHBoxLayout(); row_tools.setSpacing(10)
        btn_add = QPushButton("+"); btn_add.setObjectName("IconBtn"); btn_add.setToolTip("Add Profile")
        btn_add.clicked.connect(lambda: self.worker.add_task("PROFILE_ADD"))
        
        btn_del = QPushButton("🗑"); btn_del.setObjectName("IconBtn"); btn_del.setToolTip("Delete Profile")
        btn_del.clicked.connect(lambda: self.open_confirmation("Delete Profile", "Are you sure you want to delete this profile?", "PROFILE_DEL"))
        
        btn_menu = QPushButton("•••"); btn_menu.setObjectName("IconBtn"); btn_menu.setToolTip("More Options")
        btn_menu.clicked.connect(lambda: self.worker.add_task("PROFILE_MENU"))
        
        row_tools.addWidget(btn_add)
        row_tools.addWidget(btn_del)
        row_tools.addWidget(btn_menu)
        left_layout.addLayout(row_tools)
        
        left_layout.addSpacing(15)
        
        lbl_r = QLabel("Rename"); lbl_r.setObjectName("SectionLabel")
        left_layout.addWidget(lbl_r)
        
        self.le_rename = QLineEdit("Profile 1")
        self.le_rename.setPlaceholderText("Enter profile name")
        self.le_rename.editingFinished.connect(lambda: self.on_rename_finished(self.le_rename))
        left_layout.addWidget(self.le_rename)
        
        left_layout.addStretch(1)
        
        # Actions
        btn_rst = QPushButton("Reset to Default"); btn_rst.setObjectName("SecondaryBtn")
        btn_rst.clicked.connect(lambda: self.open_confirmation("Reset Profile", "Revert all settings to default?", "RESET"))
        left_layout.addWidget(btn_rst)
        
        left_layout.addSpacing(5)
        
        btn_app = QPushButton("Apply Changes"); btn_app.setObjectName("PrimaryBtn")
        btn_app.clicked.connect(lambda: self.worker.add_task("APPLY"))
        left_layout.addWidget(btn_app)
        
        grid_keys.addWidget(left_card, 0, 0)

        # --- CENTER PANEL (Mouse Image) ---
        center_panel = QVBoxLayout()
        center_panel.setAlignment(Qt.AlignCenter)
        self.lbl_mouse = QLabel()
        self.lbl_mouse.setAlignment(Qt.AlignCenter) 
        self.set_mouse_image(self.default_mouse)
        
        # Floating effect for mouse
        mouse_shadow = QGraphicsDropShadowEffect(); mouse_shadow.setBlurRadius(50); mouse_shadow.setColor(QColor(0,0,0,30)); mouse_shadow.setOffset(0, 20)
        self.lbl_mouse.setGraphicsEffect(mouse_shadow)
        
        center_panel.addWidget(self.lbl_mouse)
        grid_keys.addLayout(center_panel, 0, 1)

        # --- RIGHT PANEL (Key Bindings) ---
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)
        right_panel.setSpacing(20)
        right_panel.setContentsMargins(10, 20, 10, 20)
        
        lbl_k = QLabel("Button Assignments"); lbl_k.setObjectName("SectionLabel")
        right_panel.addWidget(lbl_k)
        
        keys_list = [
            ("Left Click", "KEY_BTN_1", "mouse_1.png", 0),
            ("Right Click", "KEY_BTN_2", "mouse_2.png", 120), 
            ("Middle Button", "KEY_BTN_3", "mouse_3.png", 239),
            ("Forward", "KEY_BTN_4", "mouse_4.png", 361),
            ("Backward", "KEY_BTN_5", "mouse_5.png", 480)
        ]
        
        for k, cmd, img, offset in keys_list:
            btn = QPushButton(k)
            btn.setObjectName("KeyBtn")
            # Add subtle shadow to each key button
            btn_shadow = QGraphicsDropShadowEffect(self); btn_shadow.setBlurRadius(15); btn_shadow.setColor(QColor(0,0,0,10)); btn_shadow.setOffset(0, 3)
            btn.setGraphicsEffect(btn_shadow)
            
            btn.installEventFilter(self)
            btn.setProperty("hover_img", img)
            btn.clicked.connect(lambda checked, b=btn, c=cmd, o=offset: self.open_key_menu(b, c, o))
            right_panel.addWidget(btn)
        
        right_panel.addStretch()
        grid_keys.addLayout(right_panel, 0, 2)
        
        self.stack.addWidget(page_keys)
        
        # -- Placeholders --
        self.stack.addWidget(QLabel("Performance Settings", alignment=Qt.AlignCenter))
        self.stack.addWidget(QLabel("Macro Editor", alignment=Qt.AlignCenter))

    def set_mouse_image(self, filename):
        path = os.path.join(self.base_img_path, filename)
        if os.path.exists(path):
            pix = QPixmap(path)
            self.lbl_mouse.setPixmap(pix.scaled(600, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_mouse.setText("Mouse Image Not Found")

    def create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("NavBtn") 
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(Qt.PointingHandCursor)
        
        if index == 0: btn.setChecked(True)
        nav_map = {0: "NAV_KEYS", 1: "NAV_PERF", 2: "NAV_MACRO"}
        def on_nav_click():
            self.stack.setCurrentIndex(index)
            cmd = nav_map.get(index)
            if cmd: self.worker.add_task(cmd)
        btn.clicked.connect(on_nav_click)
        return btn

    def mousePressEvent(self, event): self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            img = obj.property("hover_img")
            if img: self.set_mouse_image(img)
        elif event.type() == QEvent.Leave:
            self.set_mouse_image(self.default_mouse)
        return super().eventFilter(obj, event)

    def on_rename_finished(self, line_edit):
        new_name = line_edit.text().strip()
        if not new_name: return
        self.worker.add_task(("RENAME", new_name))
        idx = self.cb_profile.currentIndex()
        self.cb_profile.setItemText(idx, new_name)

    def open_confirmation(self, title, msg, trigger_cmd):
        self.confirm_popup = ConfirmationPopup(self, title, msg)
        def confirm_action():
            if trigger_cmd:
                self.worker.add_task(trigger_cmd)
        self.confirm_popup.accepted.connect(confirm_action)
        self.confirm_popup.show()

    def open_key_menu(self, btn, key_cmd, y_offset=0):
        self.worker.add_task(key_cmd)
        menu = QMenu(self)
        
        # ... (Menu Structure Same as before, just styled via CSS) ...
        # For brevity, reusing the logic but ensuring style applies
        
        def get_offset_coords(cmd_str):
            base = COMMANDS.get(cmd_str)
            if not base: return None
            return (base[0], base[1] + y_offset)

        structure = {
            "Basic": {"Left Click": "BASIC_LEFT", "Right Click": "BASIC_RIGHT", "Middle": "BASIC_MIDDLE", "Forward": "BASIC_FORWARD", "Backward": "BASIC_BACKWARD"},
            "Advanced": {"Double Click": "HO_DOUBLE", "Sniper": "HO_SNIPER"},
            "Media": {"Play/Pause": "MEDIA_PP", "Vol +": "MEDIA_V+", "Vol -": "MEDIA_V-"},
            "Windows": {"My Computer": "WIN_MY_PC", "Calc": "WIN_CALC", "Browser": "WIN_WEB"},
            "Disable": "ASSIGN_OFF"
        }
        
        def build_menu(parent_menu, items):
            for label, value in items.items():
                if isinstance(value, dict):
                    submenu = parent_menu.addMenu(label)
                    build_menu(submenu, value)
                else:
                    action = parent_menu.addAction(label)
                    action.triggered.connect(lambda checked, btn_id=key_cmd, cmd=value: self.attempt_assign(btn_id, cmd, y_offset))

        build_menu(menu, structure)
        menu.exec_(btn.mapToGlobal(QPoint(0, btn.height() + 5)))

    def attempt_assign(self, btn_id, new_cmd, y_offset):
        # Validation Logic (simplified for this example)
        self.assignments[btn_id] = new_cmd
        if new_cmd:
             self.worker.add_task(new_cmd)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ArmorDashboard()
    win.show()
    sys.exit(app.exec_())