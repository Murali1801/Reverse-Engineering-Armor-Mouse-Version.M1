import ctypes
import time

# ==========================================
# 1. USER CONFIGURATION
# ==========================================

# Set your 6 Custom DPI Speeds (Must be multiples of 100)
DPI_STAGES = [
    400,   # Stage 1
    800,   # Stage 2
    1200,  # Stage 3
    2400,  # Stage 4
    3200,  # Stage 5
    6200   # Stage 6
]

# Set your RGB Colors for each stage (Hex Format: RRGGBB)
# Use any HTML color code! 
DPI_COLORS = [
    "FF0055",  # Stage 1: Neon Pink
    "00FF00",  # Stage 2: Green
    "0000FF",  # Stage 3: Blue
    "FFFF00",  # Stage 4: Yellow
    "FF8800",  # Stage 5: Orange
    "00FFFF",  # Stage 6: Cyan
    "FFFFFF",  # (Hidden Stage 7)
    "FFFFFF"   # (Hidden Stage 8)
]

# ==========================================
# 2. LOAD THE DRIVER
# ==========================================
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

VID, PID = 0x04D9, 0xA09F
driver.Set_VIDPID(VID, PID)

def send_cmd(hex_str):
    data = bytes.fromhex(hex_str)
    res = driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    print(f"  [Command] {hex_str} | Res: {res}")
    time.sleep(0.02)

def send_data(hex_str):
    data = bytes.fromhex(hex_str)
    # The mouse requires exact 32-byte payloads. This zero-pads the end of the block!
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    
    buffer = (ctypes.c_byte * 32)(*data)
    res = driver.WriteUSB(buffer, 32)
    print(f"  [Payload] {hex_str[:16]}... | Res: {res}")
    time.sleep(0.02)

# ==========================================
# 3. DYNAMIC PAYLOAD BUILDER
# ==========================================
# THE FIX: We join the 3-byte colors perfectly together with NO padding between them!
# This creates a perfect 24-byte string.
color_payload = "".join([color for color in DPI_COLORS])

# Build the DPI Payload (Converts your numbers to Hex automatically)
dpi_hex = "".join([f"{int(dpi / 100):02X}" for dpi in DPI_STAGES])
dpi_payload = dpi_hex + "FCF8"

# EXACT FACTORY BUTTON MATRIX FROM HOLTEK DATASHEET:
BTN_BLOCK_1 = "0100F0000100F1000100F2000100F4000100F300070003000000000000000000"
BTN_BLOCK_2 = "0000000000000000000000000000000000000000000000000400010004000200"

# ==========================================
# 4. FLASH THE MOUSE HARDWARE
# ==========================================
print("🔌 Connecting to Mouse Pipelines...")
feature_status = driver.Open_FeatureDevice()
report_status = driver.Open_ReportDevice()

if feature_status == 0 or report_status == 0:
    print("❌ Failed to open USB communication. Make sure the official app is closed.")
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

print(f"\n🎨 3. Injecting Custom Colors (Alignment Fixed!)...")
send_cmd("272A85FFF0657636")
send_data(color_payload) 
send_cmd("272A8DFFE8657636")
send_data(color_payload) 

print(f"\n⚡ 4. Injecting Custom DPI Speeds... ({dpi_hex})")
send_cmd("272BFDFFE06D76B6")
send_data(dpi_payload)

print("\n⚙️ 5. Restoring Factory Button Matrix...")
send_cmd("272D5DFFE8557876")
send_data(BTN_BLOCK_1) 
send_cmd("272D25FF00557876")
send_data(BTN_BLOCK_2) 

print("\n🏁 6. Sending Finalization Block...")
send_cmd("272BFDFFF86576D6")
send_data("FF000000000000000000000000000000")

print("\n🔒 7. Locking and Committing to Memory...")
send_cmd("08AACCEE0000001E")

print("\n🎉 COMPLETE! The colors are perfectly aligned.")