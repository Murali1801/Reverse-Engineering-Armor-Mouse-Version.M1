import ctypes
import time

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE EVERYTHING HERE)
# =====================================================================

DPI_STAGES = [
    400,   # Stage 1
    800,   # Stage 2
    1200,  # Stage 3
    2400,  # Stage 4
    3200,  # Stage 5
    6200   # Stage 6
]

DPI_COLORS = [
    "FF0055",  # Stage 1: Neon Pink
    "00FF00",  # Stage 2: Green
    "0000FF",  # Stage 3: Blue
    "FFFF00",  # Stage 4: Yellow
    "FF8800",  # Stage 5: Orange
    "00FFFF"   # Stage 6: Cyan
]

# --- BUTTON SET 1 (Main Mouse Buttons) ---
# I HAVE CHANGED SLOTS 4 AND 5 TO MEDIA KEYS FOR THIS TEST!
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click
    "0100F100",  # Slot 2: Right Click
    "0100F200",  # Slot 3: Middle Click
    "0300E900",  # Slot 4: VOLUME UP (Was Forward)
    "03009201",  # Slot 5: PLAY / PAUSE (Was Back)
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
    "04000100",  # Slot 15: Scroll Wheel Up
    "04000200"   # Slot 16: Scroll Wheel Down
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
    data = bytes.fromhex(hex_str)
    driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    time.sleep(0.02)

def send_data(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    
    buffer = (ctypes.c_byte * 32)(*data)
    driver.WriteUSB(buffer, 32)
    time.sleep(0.02)

# =====================================================================
# 3. DYNAMIC PAYLOAD BUILDER
# =====================================================================
color_payload = "".join([color for color in DPI_COLORS])
dpi_payload = "".join([f"{int(dpi / 100):02X}" for dpi in DPI_STAGES]) + "7C78"
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

print("\n🔓 Waking up Hardware...")
send_cmd("08AACCEE0000001E")
time.sleep(0.05)
send_cmd("252BA5FFF0E0E6EE")

print("🛠️ Sending Hardware Initialization Registers...")
send_cmd("272BDDFFE8D57676")
send_cmd("272BD5FFE8ED7676")
send_cmd("272B7DFFD01D7676")
send_cmd("272B9D0498457676")
send_cmd("272B5DFFD0524E8E")

print("🎨 Injecting Custom Colors...")
send_cmd("272A85FFF0657636")
send_data(color_payload) 
send_cmd("272A8DFFE8657636")
send_data(color_payload) 

print(f"⚡ Injecting Custom DPI Speeds...")
send_cmd("272BFDFFE06D76B6")
send_data(dpi_payload)

print("⚙️ Injecting Custom Button Mappings (MEDIA KEYS ADDED!)...")
send_cmd("272D5DFFE8557876")
send_data(btn_payload_1) 
send_cmd("272D25FF00557876")
send_data(btn_payload_2) 

print("🏁 Sending Finalization Block...")
send_cmd("272BFDFFF86576D6")
send_data("FF000000000000000000000000000000")

print("🔒 Locking and Committing to Memory...")
send_cmd("08AACCEE0000001E")

print("\n🎉 COMPLETE! Press your side buttons to change your volume and pause music!")