import ctypes
import time

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE EVERYTHING HERE)
# =====================================================================

# --- POLLING RATE ---
# Uncomment ONLY ONE of the exact hardware hex strings below:
POLLING_RATE_CMD = "01010000000000B6"  # 1000Hz (1ms) - Best for Gaming
# POLLING_RATE_CMD = "01020000000000FC"  # 500Hz  (2ms) - Factory Default
# POLLING_RATE_CMD = "01040000000000FA"  # 250Hz  (4ms)
# POLLING_RATE_CMD = "01080000000000F6"  # 125Hz  (8ms) - Battery Saver

# --- DPI SPEEDS ---
# Set your 6 Custom DPI Speeds (Must be multiples of 100)
DPI_STAGES = [
    400,   # Stage 1
    800,   # Stage 2
    1200,  # Stage 3
    2400,  # Stage 4
    3200,  # Stage 5
    6200   # Stage 6
]

# --- DPI COLORS ---
# Set your 6 RGB Colors (Use any HTML Hex Color Code: RRGGBB)
DPI_COLORS = [
    "FF0055",  # Stage 1: Neon Pink
    "00FF00",  # Stage 2: Green
    "0000FF",  # Stage 3: Blue
    "FFFF00",  # Stage 4: Yellow
    "FF8800",  # Stage 5: Orange
    "00FFFF"   # Stage 6: Cyan
]

# --- BUTTON SET 1 (Main Mouse Buttons) ---
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click
    "0100F100",  # Slot 2: Right Click
    "0100F200",  # Slot 3: Middle Click
    "0100F400",  # Slot 4: Forward (Side Button 1)
    "0100F300",  # Slot 5: Back (Side Button 2)
    "07000300",  # Slot 6: DPI Loop Button
    "00000000",  # Slot 7: Unused
    "00000000"   # Slot 8: Unused
]

# --- BUTTON SET 2 (Scroll Wheel & Extras) ---
BUTTONS_BLOCK_2 = [
    "00000000",  # Slot 9: Unused
    "00000000",  # Slot 10: Unused
    "00000000",  # Slot 11: Unused
    "00000000",  # Slot 12: Unused
    "00000000",  # Slot 13: Unused
    "00000000",  # Slot 14: Unused
    "04000100",  # Slot 15: Scroll Wheel Up (DO NOT CHANGE)
    "04000200"   # Slot 16: Scroll Wheel Down (DO NOT CHANGE)
]


# =====================================================================
# 2. LOAD THE DRIVER (DO NOT EDIT BELOW THIS LINE)
# =====================================================================
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

VID, PID = 0x04D9, 0xA09F
driver.Set_VIDPID(VID, PID)

def send_cmd(hex_str):
    """Sends 8-byte Command Headers via SetFeature"""
    data = bytes.fromhex(hex_str)
    res = driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    print(f"  [Command] {hex_str} | Res: {res}")
    time.sleep(0.02)

def send_data(hex_str):
    """Sends 32-byte Data Payloads via WriteUSB"""
    data = bytes.fromhex(hex_str)
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    
    buffer = (ctypes.c_byte * 32)(*data)
    res = driver.WriteUSB(buffer, 32)
    print(f"  [Payload] {hex_str[:16]}... | Res: {res}")
    time.sleep(0.02)

# =====================================================================
# 3. DYNAMIC PAYLOAD BUILDER
# =====================================================================
# Tightly pack the 6 colors together (18 bytes)
color_payload = "".join([color for color in DPI_COLORS])

# Build the 6-Stage DPI Payload, appending the 7C78 Hardware Calibration bytes
dpi_payload = "".join([f"{int(dpi / 100):02X}" for dpi in DPI_STAGES]) + "7C78"

# Join the button lists into exact 32-byte strings
btn_payload_1 = "".join(BUTTONS_BLOCK_1)
btn_payload_2 = "".join(BUTTONS_BLOCK_2)

# =====================================================================
# 4. FLASH THE MOUSE HARDWARE
# =====================================================================
print("🔌 Connecting to Mouse Pipelines...")
feature_status = driver.Open_FeatureDevice()
report_status = driver.Open_ReportDevice()

if feature_status == 0 or report_status == 0:
    print("❌ Failed to open USB communication. Close the official app!")
    exit()

print("\n🔓 1. Waking up Hardware...")
send_cmd("08AACCEE0000001E")
time.sleep(0.05)
send_cmd("252BA5FFF0E0E6EE")

print("\n🛠️ 2. Sending Hardware Initialization Registers...")
send_cmd("272BDDFFE8D57676")
send_cmd("272BD5FFE8ED7676")
send_cmd("272B7DFFD01D7676")
send_cmd("272B9D0498457676")
send_cmd("272B5DFFD0524E8E")

print(f"\n⏱️ 3. Setting Polling Rate...")
send_cmd(POLLING_RATE_CMD)

print("\n🎨 4. Injecting Custom Colors...")
send_cmd("272A85FFF0657636")
send_data(color_payload) 
send_cmd("272A8DFFE8657636")
send_data(color_payload) 

print(f"\n⚡ 5. Injecting Custom DPI Speeds...")
send_cmd("272BFDFFE06D76B6")
send_data(dpi_payload)

print("\n⚙️ 6. Injecting Custom Button Mappings...")
send_cmd("272D5DFFE8557876")
send_data(btn_payload_1) 
send_cmd("272D25FF00557876")
send_data(btn_payload_2) 

print("\n🏁 7. Sending Finalization Block...")
send_cmd("272BFDFFF86576D6")
send_data("FF000000000000000000000000000000")

print("\n🔒 8. Locking and Committing to Memory...")
send_cmd("08AACCEE0000001E")

print("\n🎉 COMPLETE! Your mouse has been fully programmed.")