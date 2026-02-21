import sys
import os
import time

# 🛑 CRITICAL: COM initialization for thread safety
sys.coinit_flags = 2 

from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QLabel, QFrame, QStackedWidget, 
                             QComboBox, QLineEdit, QSlider, QCheckBox, QGridLayout, QSpacerItem, QSizePolicy, QMenu, QAction, QMainWindow)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QEvent, QSize
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QFont

from armor_api import ArmorAPI, COMMANDS

# ==========================================
# 🎨 THEME CONFIGURATION
# ==========================================
STYLESHEET = """
/* Global Styles */
QWidget { 
    font-family: 'Arial', sans-serif; 
    font-size: 14px; 
    color: #333; 
}

/* 
   ==========================================================================
   Attributes for helper classes (used in code, not CSS selectors directly)
   ==========================================================================
   Note: WA_TranslucentBackground is set in Python.
*/

/* Top Bar */
QLabel#LogoTitle { 
    color: white; 
    font-size: 40px; 
    font-weight: bold; 
    margin-left: 20px;
    letter-spacing: 2px;
}

/* Navigation Buttons (Ref: main_btn_style) */
QPushButton#NavBtn { 
    background: transparent; 
    border: 2px solid transparent; 
    color: #000000; /* XML: textcolor="#FF000000" */
    font-family: 'Arial';
    font-size: 17px; /* XML: font="1" -> size 17 */
    min-width: 180px;
    min-height: 50px;
    border-radius: 0px;
    text-align: center;
    font-weight: normal;
}
QPushButton#NavBtn:checked { 
    background-color: rgba(38, 187, 238, 0.4); /* Stronger visibility */
    border: 2px solid #26bbee; /* XML: hottextcolor="#0xFF26bbee" */
    border-style: solid;
    color: #26bbee; 
    font-weight: bold;
}
QPushButton#NavBtn:hover:!checked {
    color: #26bbee;
    border: 2px solid transparent;
}

/* Section Labels */
QLabel#SectionLabel { 
    font-size: 13px; 
    color: #000000; 
    margin-bottom: 3px; 
}

/* Inputs (Ref: edit_style / combo_style) */
QComboBox, QLineEdit { 
    border: 1px solid #999; 
    padding: 5px; 
    background: #FFFFFF; /* XML: bkcolor="#FFFFFFFF" */
    font-size: 12px; /* XML: font="3" -> size 12 */
    border-radius: 0px;
    color: #000000;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid #333; margin-right: 5px; }


/* Small Icon Buttons (+, -, ...) */
QPushButton#IconBtn {
    border: 1px solid #5F5F5F;
    background-color: white; 
    font-weight: bold;
    font-size: 16px;
    min-height: 30px;
    color: #26bbee; 
    border-radius: 0px;
}
QPushButton#IconBtn:hover { 
    background-color: #F0F0F0;
    border-color: #26bbee;
}

/* Action Buttons (Reset/Apply) (Ref: bottom_button) */
QPushButton#ActionBtn { 
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid #5F5F5F; 
    padding: 8px; 
    font-size: 14px;
    color: #5F5F5F; /* XML: textcolor="#FF5F5F5F" */
    border-radius: 0px;
    text-align: center;
    min-height: 30px;
    min-width: 80px;
}
QPushButton#ActionBtn:hover { 
    background: rgba(255, 255, 255, 1.0); 
    color: #26bbee; /* XML: hottextcolor="#0xFF26bbee" */
    border-color: #26bbee;
}

/* Key Binding Buttons (Ref: mouse_key_style) */
QPushButton#KeyBtn { 
    background-color: rgba(255, 255, 255, 0.5); 
    border: 1px solid #999;
    color: #000000; /* XML: textcolor="#FF000000" */
    padding: 10px; 
    text-align: center;
    font-family: 'Arial';
    font-size: 15px; /* XML: font="0" -> size 15 */
    min-width: 220px;
    border-radius: 2px;
    margin-bottom: 5px;
}
QPushButton#KeyBtn:hover { 
    background-color: rgba(38, 187, 238, 0.2);
    border: 1px solid #26bbee; /* XML: hot/pushed */
    color: #26bbee;
}

/* Menus */
QMenu {
    background-color: #FAFAFA;
    border: 1px solid #CCC;
    color: #333;
}
QMenu::item {
    padding: 5px 20px 5px 20px;
}
QMenu::item:selected {
    background-color: #26bbee;
    color: white;
}

/* Window Controls */
QPushButton#CloseBtn, QPushButton#MinBtn { 
    color: white; 
    font-weight: bold; 
    font-size: 16px; 
    background: transparent; 
    border: none; 
}
QPushButton#CloseBtn:hover { color: red; }

/* Popup Styles */
QFrame#PopupContainer {
    background-color: #222;
    border: 2px solid #26bbee;
}
QLabel#PopupTitle {
    color: #26bbee;
    font-size: 18px;
    font-weight: bold;
}
QLabel#PopupMessage {
    color: white;
    font-size: 15px;
}
QPushButton.popupBtn {
    background: transparent;
    border: 1px solid #26bbee;
    color: white;
    min-width: 100px;
    min-height: 30px;
    font-size: 13px;
}
QPushButton.popupBtn:hover {
    background-color: rgba(38, 187, 238, 0.2);
}
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
                # Task can be:
                # 1. Command String: "NAV_KEYS"
                # 2. Coordinate Tuple: (x, y)
                # 3. Rename Tuple: ("RENAME", "New Name")
                
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
        self.setFixedSize(600, 350)
        # Center in parent
        self.move(parent.width() // 2 - 300, parent.height() // 2 - 175)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 40)
        
        # Header Row (Title + Close)
        header = QHBoxLayout()
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("PopupTitle")
        header.addWidget(lbl_title)
        header.addStretch()
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("color: white; border: none; font-size: 18px;")
        btn_close.clicked.connect(self.hide)
        header.addWidget(btn_close)
        layout.addLayout(header)
        
        layout.addStretch(1)
        
        # Message
        lbl_msg = QLabel(message_text)
        lbl_msg.setObjectName("PopupMessage")
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)
        
        layout.addStretch(1)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setAlignment(Qt.AlignCenter)
        
        btn_ok = QPushButton("Ok")
        btn_ok.setProperty("class", "popupBtn")
        btn_ok.clicked.connect(self.on_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "popupBtn")
        btn_cancel.clicked.connect(self.hide)
        
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.resize(1280, 750)
        
        self.setStyleSheet(STYLESHEET)
            
        # 1. Central Widget is just a container for the layout
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        # 2. Main Layout (Stacked to handle background layer + content layer)
        # However, a simpler approach for QMainWindow is setting a background on the central widget
        # OR using a layout that places the background behind everything.
        
        # Let's use a QGridLayout on the central widget.
        # We will add a QLabel for the background at (0,0) spanning everything.
        # And another layout for content at (0,0) spanning everything.
        
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # --- BACKGROUND LAYER ---
        self.bg_label = QLabel(self)
        try:
            bg_path = os.path.abspath("res/skins/bk/bk.jpg")
            if os.path.exists(bg_path):
                pixmap = QPixmap(bg_path)
                self.bg_label.setPixmap(pixmap)
                self.bg_label.setScaledContents(True)
            else:
                self.bg_label.setText("Background Image Not Found")
                self.bg_label.setStyleSheet("background-color: grey;")
        except Exception as e:
            print(f"Error loading background: {e}")
            self.bg_label.setStyleSheet("background-color: grey;")
            
        # Add background to grid, spanning row 0, col 0
        main_layout.addWidget(self.bg_label, 0, 0)

        # --- CONTENT LAYER ---
        # A widget to hold all content, placed ON TOP of the background
        content_container = QWidget()
        content_container.setObjectName("ContentContainer")
        # Ensure it's transparent
        content_container.setAttribute(Qt.WA_TranslucentBackground)
        content_container.setStyleSheet("background: transparent; border: none;")
        
        # Add to grid, spanning same row/col as background so they overlap
        main_layout.addWidget(content_container, 0, 0)

        # Now build the UI inside content_container
        layout_content = QVBoxLayout(content_container)
        layout_content.setContentsMargins(50, 30, 50, 30)
        layout_content.setSpacing(10)

        # === TOP BAR ===
        top_layout = QHBoxLayout()
        lbl_logo = QLabel("armor"); lbl_logo.setObjectName("LogoTitle")
        top_layout.addWidget(lbl_logo)
        
        # XML Spacing: 170px from Logo to Keys
        top_layout.addSpacing(170)

        # Nav Buttons
        nav_container = QHBoxLayout()
        nav_container.setSpacing(130) # XML Spacing: 130px between Keys/Perf/Macro
        nav_container.addWidget(self.create_nav_btn("Keys", 0))
        nav_container.addWidget(self.create_nav_btn("Performance", 1))
        nav_container.addWidget(self.create_nav_btn("Macro", 2))
        
        top_layout.addLayout(nav_container)
        top_layout.addStretch(1) # Stretch pushes rest to right
        top_layout.addStretch(1)

        # Win Controls
        btn_min = QPushButton("─"); btn_min.setObjectName("MinBtn"); btn_min.clicked.connect(self.showMinimized)
        btn_close = QPushButton("✕"); btn_close.setObjectName("CloseBtn"); btn_close.clicked.connect(self.close)
        top_layout.addWidget(btn_min)
        top_layout.addSpacing(10)
        top_layout.addWidget(btn_close)
        layout_content.addLayout(top_layout)
        
        layout_content.addSpacing(40)

        # === STACKED PAGES ===
        self.stack = QStackedWidget()
        self.stack.setAttribute(Qt.WA_TranslucentBackground) # Transparent stack
        self.stack.setStyleSheet("background: transparent; border: none;")
        layout_content.addWidget(self.stack)

        # -- PAGE 0: KEYS --
        page_keys = QWidget()
        page_keys.setAttribute(Qt.WA_TranslucentBackground)
        page_keys.setStyleSheet("background: transparent; border: none;")
        
        grid_keys = QGridLayout(page_keys)
        grid_keys.setContentsMargins(20, 0, 20, 20)
        grid_keys.setColumnStretch(0, 3); grid_keys.setColumnStretch(1, 5); grid_keys.setColumnStretch(2, 3)

        # Left Column
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignTop); left_panel.setSpacing(15)
        
        lbl_s = QLabel("Select A Profile"); lbl_s.setObjectName("SectionLabel")
        left_panel.addWidget(lbl_s)
        
        self.cb_profile = QComboBox(); self.cb_profile.addItems(["Profile3", "Default", "Game Mode"])
        left_panel.addWidget(self.cb_profile)
        
        # Icons
        row_ico = QHBoxLayout(); row_ico.setSpacing(10)
        btn_add = QPushButton("+"); btn_add.setObjectName("IconBtn")
        btn_add.clicked.connect(lambda: self.worker.add_task("PROFILE_ADD"))
        row_ico.addWidget(btn_add)
        
        btn_del = QPushButton("⟰"); btn_del.setObjectName("IconBtn")
        btn_del.clicked.connect(lambda: self.open_confirmation("Warning!", "Do you really want to delete this profile?", "PROFILE_DEL"))
        row_ico.addWidget(btn_del)
        
        btn_menu = QPushButton("..."); btn_menu.setObjectName("IconBtn")
        btn_menu.clicked.connect(lambda: self.worker.add_task("PROFILE_MENU"))
        row_ico.addWidget(btn_menu)
        left_panel.addLayout(row_ico)
        
        lbl_r = QLabel("Rename Profile"); lbl_r.setObjectName("SectionLabel")
        left_panel.addWidget(lbl_r)
        
        self.le_rename = QLineEdit("Profile3")
        self.le_rename.editingFinished.connect(lambda: self.on_rename_finished(self.le_rename))
        left_panel.addWidget(self.le_rename)
        
        left_panel.addSpacing(10)
        btn_rst = QPushButton("Reset"); btn_rst.setObjectName("ActionBtn")
        btn_rst.clicked.connect(lambda: self.open_confirmation("Warning!", "Do you really want to reset this profile to default setting?", "RESET"))
        left_panel.addWidget(btn_rst)
        
        left_panel.addStretch()
        btn_app = QPushButton("Apply"); btn_app.setObjectName("ActionBtn")
        btn_app.clicked.connect(lambda: self.worker.add_task("APPLY"))
        left_panel.addWidget(btn_app)
        
        grid_keys.addLayout(left_panel, 0, 0)

        # Center Column (Mouse)
        center_panel = QVBoxLayout()
        center_panel.setAlignment(Qt.AlignCenter)
        self.lbl_mouse = QLabel()
        self.lbl_mouse.setAlignment(Qt.AlignCenter)
        self.set_mouse_image(self.default_mouse)
        center_panel.addWidget(self.lbl_mouse)
        grid_keys.addLayout(center_panel, 0, 1)

        # Right Column (Keys)
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignTop)
        right_panel.addSpacing(60) # Spacing from top
        right_panel.setSpacing(35)
        
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
            btn.installEventFilter(self)
            btn.setProperty("hover_img", img)
            btn.clicked.connect(lambda checked, b=btn, c=cmd, o=offset: self.open_key_menu(b, c, o))
            right_panel.addWidget(btn)
        
        right_panel.addStretch()
        grid_keys.addLayout(right_panel, 0, 2)
        
        self.stack.addWidget(page_keys)
        
        # -- PAGE 1: PERFORMANCE (Placeholder for now) --
        page_perf = QWidget()
        page_perf.setAttribute(Qt.WA_TranslucentBackground)
        self.stack.addWidget(page_perf)
        
        # -- PAGE 2: MACRO --
        page_macro = QLabel("Macro")
        self.stack.addWidget(page_macro)


    def set_mouse_image(self, filename):
        path = os.path.join(self.base_img_path, filename)
        if os.path.exists(path):
            pix = QPixmap(path)
            self.lbl_mouse.setPixmap(pix.scaled(800, 700, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("NavBtn") # Use ObjectName for robust styling
        btn.setAttribute(Qt.WA_StyledBackground, True) # Force background painting
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        
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
        if hasattr(self, 'last_renamed_text') and self.last_renamed_text == new_name:
            return
        self.last_renamed_text = new_name
        self.worker.add_task(("RENAME", new_name))
        
        # Update Combo
        idx = self.cb_profile.currentIndex()
        self.cb_profile.setItemText(idx, new_name)

    def open_confirmation(self, title, msg, trigger_cmd):
        self.confirm_popup = ConfirmationPopup(self, title, msg)
        def confirm_action():
            if trigger_cmd:
                self.worker.add_task(trigger_cmd)
                QTimer.singleShot(200, lambda: self.worker.add_task("POPUP_OK"))
        self.confirm_popup.accepted.connect(confirm_action)
        self.confirm_popup.show()

    def open_key_menu(self, btn, key_cmd, y_offset=0):
        # 1. First trigger the click on the button itself (to open the menu in the real app)
        self.worker.add_task(key_cmd)
        
        # 2. Show our overlay menu
        menu = QMenu(self)
        
        # Helper to calculate new coords
        def get_offset_coords(cmd_str):
            base = COMMANDS.get(cmd_str)
            if not base: return None
            return (base[0], base[1] + y_offset)

        # Define the structure
        # Key: Label, Value: (API_CMD or SubMenuDict)
        structure = {
            "Basic Function": {
                "Left Click": "BASIC_LEFT",
                "Right Click": "BASIC_RIGHT",
                "Middle Button": "BASIC_MIDDLE",
                "Forward": "BASIC_FORWARD",
                "Backward": "BASIC_BACKWARD",
                "Scroll Up": "BASIC_SCROLL_UP", 
                "Scroll Down": "BASIC_SCROLL_DOWN"
            },
            "High Order Function": {
                "Double Click": "HIGH_ORDER_DOUBLE",
                "Three Click": "HIGH_ORDER_THREE",
                "Light Mode Switch": "HIGH_ORDER_LIGHT",
                "Sniper Key": "HIGH_ORDER_SNIPER"
            },
            "Button Off": "ASSIGN_OFF",
            "Shortcut": "ASSIGN_SHORTCUT",
            "Select A Macro": "ASSIGN_MACRO",
            "DPI": {
                "DPI Cycle": "DPI_CYCLE",
                "DPI +": "DPI_PLUS",
                "DPI -": "DPI_MINUS"
            },
            "Report": {
                "Report Cycle": "REPORT_CYCLE",
                "Report +": "REPORT_PLUS",
                "Report -": "REPORT_MINUS"
            },
            "Multimedia": {
                "Media Player": "MEDIA_PLAYER",
                "Play / Pause": "MEDIA_PLAY_PAUSE",
                "Stop": "MEDIA_STOP", 
                "Previous Track": "MEDIA_PREV",
                "Next Track": "MEDIA_NEXT", 
                "Volume +": "MEDIA_VOL_PLUS",
                "Volume -": "MEDIA_VOL_MINUS", 
                "Mute": "MEDIA_MUTE"
            },
            "Windows": {
                "Browser Home": "WIN_HOME",
                "Browser Favorites": "WIN_FAV", 
                "Browser Forward": "WIN_FWD",
                "Browser Backward": "WIN_BACK", 
                "Browser Stop": "WIN_STOP",
                "Browser Refresh": "WIN_REFRESH",
                "Browser Search": "WIN_SEARCH", 
                "Email": "WIN_EMAIL",
                "Calculator": "WIN_CALC", 
                "My Computer": "WIN_MY_PC"
            },
            "Office": {
                "Cut": "OFFICE_CUT",
                "Copy": "OFFICE_COPY", 
                "Paste": "OFFICE_PASTE",
                "Open": "OFFICE_OPEN", 
                "Save": "OFFICE_SAVE",
                "Find": "OFFICE_FIND", 
                "Redo": "OFFICE_REDO",
                "Select All": "OFFICE_SELECT_ALL", 
                "New": "OFFICE_NEW", 
                "Print": "OFFICE_PRINT"
            },
            "Advance Function": {
                "Swap Windows": "ADV_SWAP",
                "Close Window": "ADV_CLOSE", 
                "Show Desktop": "ADV_DESKTOP",
                "Lock PC": "ADV_LOCK", 
                "Run Command": "ADV_RUN"
            }
        }
        
        # Helper to build recursive menus
        def build_menu(parent_menu, items):
            for label, value in items.items():
                if isinstance(value, dict):
                    # It's a submenu
                    submenu = parent_menu.addMenu(label)
                    
                    assign_keys = {
                        "Basic Function": "ASSIGN_BASIC",
                        "High Order Function": "ASSIGN_HIGH_ORDER",
                        "DPI": "ASSIGN_DPI",
                        "Report": "ASSIGN_REPORT",
                        "Multimedia": "ASSIGN_MEDIA",
                        "Windows": "ASSIGN_WINDOWS",
                        "Office": "ASSIGN_OFFICE",
                        "Advance Function": "ASSIGN_ADVANCE"
                    }
                    
                    assign_cmd = assign_keys.get(label)
                    build_menu(submenu, value)
                    
                    # When this submenu is about to show, we trigger the assign command
                    if assign_cmd:
                        # Convert to coords with offset
                        target_coords = get_offset_coords(assign_cmd)
                        if target_coords:
                            submenu.aboutToShow.connect(lambda c=target_coords: self.worker.add_task(c))

                else:
                    # Leaf item (The actual function assignment)
                    action = parent_menu.addAction(label)
                    
                    # We need to capture the assignment attempt
                    # value is the COMMAND string (e.g., "BASIC_LEFT", "WIN_CALC")
                    action.triggered.connect(lambda checked, btn_id=key_cmd, cmd=value: self.attempt_assign(btn_id, cmd, y_offset))

        build_menu(menu, structure)
        
        # Position menu at button
        menu.exec_(btn.mapToGlobal(QPoint(btn.width(), 0)))

    def attempt_assign(self, btn_id, new_cmd, y_offset):
        """
        Validates if the assignment is allowed.
        Constraint: At least one button MUST be 'Left Click' (BASIC_LEFT).
        """
        # 1. Check if we are changing a button that is CURRENTLY Left Click
        current_cmd = self.assignments.get(btn_id)
        
        if current_cmd == "BASIC_LEFT" and new_cmd != "BASIC_LEFT":
            # 2. Check if ANY OTHER button is Left Click
            other_has_left = False
            for bid, cmd in self.assignments.items():
                if bid != btn_id and cmd == "BASIC_LEFT":
                    other_has_left = True
                    break
            
            if not other_has_left:
                # VIOLATION! Show Warning Popup
                self.open_confirmation("Warning!", 'At least one button must be "Left Click" Or "Send Gun"!', None)
                return

        # 3. If valid, proceed with assignment
        self.assignments[btn_id] = new_cmd
        
        # Execute the command
        target_coords = None
        base = COMMANDS.get(new_cmd)
        if base:
            target_coords = (base[0], base[1] + y_offset)
            
        if target_coords:
            self.worker.add_task(target_coords)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ArmorDashboard()
    win.show()
    sys.exit(app.exec_())