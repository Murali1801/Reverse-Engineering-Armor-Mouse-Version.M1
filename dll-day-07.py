import ctypes
import time

# ==========================================
# 1. USER CONFIGURATION
# ==========================================

# Set your DPI stages (Must be multiples of 100)
DPI_STAGES = [
    400,   # Stage 1
    800,   # Stage 2
    1200,  # Stage 3
    2400,  # Stage 4
    3200,  # Stage 5
    6200   # Stage 6
]

# Set your RGB Colors for each stage (Hex Format: RRGGBB)
DPI_COLORS = [
    "0000FF",  # Stage 1: PURE BLUE (Testing the change!)
    "00FF00",  # Stage 2: Green
    "FF0000",  # Stage 3: Red
    "FFFF00",  # Stage 4: Yellow
    "00FFFF",  # Stage 5: Cyan
    "FF00FF",  # Stage 6: Magenta
    "FFFFFF",  # Slot 7 (Hardware Padding)
    "FFFFFF"   # Slot 8 (Hardware Padding)
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

def send_header(hex_str):
    data = bytes.fromhex(hex_str)
    driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    time.sleep(0.02)

def send_payload(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    time.sleep(0.02)

# ==========================================
# 3. DYNAMICALLY BUILD THE PAYLOADS
# ==========================================

# Build the 32-byte Color Payload (RRGGBB + 00 padding per color)
color_payload = "".join([color + "00" for color in DPI_COLORS])

# Build the 16-byte DPI Payload 
dpi_hex = "".join([f"{int(dpi / 100):02X}" for dpi in DPI_STAGES])
dpi_payload = dpi_hex + "7C780000000000000000000000000000"

print("🔌 Connecting to Mouse Pipelines...")
feature_status = driver.Open_FeatureDevice()
report_status = driver.Open_ReportDevice()

if feature_status == 0 or report_status == 0:
    print("❌ Failed to open USB communication. Make sure the official app is closed!")
    exit()

print("\n🔓 1. Waking up Hardware (Handshake)...")
send_header("08AACCEE0000001E")
time.sleep(0.05)
send_header("252BA5FFF0E0E6EE")

print(f"\n🎨 2. INJECTING CUSTOM RGB COLORS...")
send_header("272A85FFF0657636")
send_payload(color_payload) # Injecting Block 1

print("🎨 3. Sending LED Color Block 2...")
send_header("272A8DFFE8657636")
send_payload(color_payload) # Injecting Block 2

print(f"\n⚡ 4. INJECTING CUSTOM DPI BLOCK... ({dpi_hex})")
send_header("272BFDFFE06D76B6")
send_payload(dpi_payload)

print("\n⚙️ 5. Sending Parameters Block 1...")
send_header("272D5DFFE8557876")
send_payload("0100F0000100F1000100F2000100F40005000500050004000500060000000000")

print("⚙️ 6. Sending Parameters Block 2...")
send_header("272D25FF00557876")
send_payload("0C0000000100F1000100F2000100F40000000000000000000000000000000000")

print("\n🏁 7. Sending Finalization Block...")
send_header("272BFDFFF86576D6")
send_payload("FF000000000000000000000000000000FF000000000000000000000000000000")

print("\n🔒 8. Locking and Committing to Memory...")
send_header("08AACCEE0000001E")

print("\n🎉 COMPLETE! Press your DPI cycle button!")