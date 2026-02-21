import ctypes
import time

# ==========================================
# 1. USER CONFIGURATION (CUSTOM DPI)
# ==========================================
# Set your 6 DPI stages here! (Must be multiples of 100)
DPI_STAGES = [
    400,   # Stage 1 
    800,   # Stage 2 
    1200,  # Stage 3 
    2400,  # Stage 4 
    3200,  # Stage 5 
    6200   # Stage 6 
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
    """Sends the 8-byte Command Header via SetFeature"""
    data = bytes.fromhex(hex_str)
    buffer = (ctypes.c_byte * 8)(*data)
    result = driver.SetFeature(buffer, 8)
    print(f"  [Header]  {hex_str} | Result: {result}")
    time.sleep(0.02)

def send_payload(hex_str):
    """Sends the 32-byte Data Payload via WriteUSB"""
    data = bytes.fromhex(hex_str)
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    
    buffer = (ctypes.c_byte * 32)(*data)
    result = driver.WriteUSB(buffer, 32)
    print(f"  [Payload] {hex_str[:16]}... | Result: {result}")
    time.sleep(0.02)

# Convert your DPI numbers to hex
dpi_hex = "".join([f"{int(dpi / 100):02X}" for dpi in DPI_STAGES])
# Append the hardware limit bytes (7C 78) we found in your dump!
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

print("\n🎨 2. Sending LED Color Block 1...")
send_header("272A85FFF0657636")
send_payload("FF000000FF000000FFFFFF00FF00FF00FF000000FF000000FFFFFF00FF00FF00")

print("\n🎨 3. Sending LED Color Block 2...")
send_header("272A8DFFE8657636")
send_payload("FF000000FF000000FFFFFF00FF00FF00FF000000FF000000FFFFFF00FF00FF00")

print(f"\n⚡ 4. INJECTING CUSTOM DPI BLOCK... ({dpi_hex})")
send_header("272BFDFFE06D76B6")
send_payload(dpi_payload) 

print("\n⚙️ 5. Sending Parameters Block 1...")
send_header("272D5DFFE8557876")
send_payload("0100F0000100F1000100F2000100F40005000500050004000500060000000000")

print("\n⚙️ 6. Sending Parameters Block 2...")
send_header("272D25FF00557876")
send_payload("0C0000000100F1000100F2000100F40000000000000000000000000000000000")

print("\n🏁 7. Sending Finalization Block...")
send_header("272BFDFFF86576D6")
send_payload("FF000000000000000000000000000000FF000000000000000000000000000000")

print("\n🔒 8. Locking and Committing to Memory...")
send_header("08AACCEE0000001E")

print("\n🎉 COMPLETE! The State Machine has been satisfied.")