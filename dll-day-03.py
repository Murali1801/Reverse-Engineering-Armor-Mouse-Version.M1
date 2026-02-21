import ctypes
import time
import json

# --- CONFIGURATION ---
VID = 0x04D9  #
PID = 0xA09F  #

# --- LOAD DLL ---
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

# Define Function Signatures
driver.Set_VIDPID.argtypes = [ctypes.c_int, ctypes.c_int]
driver.SetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.SetFeature.restype = ctypes.c_int
driver.WriteUSB.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.WriteUSB.restype = ctypes.c_int
driver.GetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.GetFeature.restype = ctypes.c_int
driver.Open_FeatureDevice.restype = ctypes.c_int
driver.Open_ReportDevice.restype = ctypes.c_int

def send_feature(hex_str):
    """Sends an 8-byte Feature Report (Setup Data)."""
    data = bytes.fromhex(hex_str)
    return driver.SetFeature((ctypes.c_byte * 8)(*data), 8)

# --- 1. EXTRACT ONLY THE CONFIGURATION DATA ---
print("📂 Extracting precisely 68 configuration packets from json.json...")
try:
    with open('json.json', 'r', encoding='utf-8') as f:
        capture_data = json.load(f)
except Exception as e:
    print(f"❌ Error loading json.json: {e}")
    exit()

# We need to find the specific start of the configuration burst
# Packet 271 in json3.json starts with this data:
target_start_hex = "ff000000ff000000ffffff00ff00ff00ffffff8000ffffff0000000000000000"

config_payloads = []
found_start = False
for pkt in capture_data:
    layers = pkt.get('_source', {}).get('layers', {})
    hid_data = layers.get('usbhid.data', '').replace(':', '')
    ep = layers.get('usb', {}).get('usb.endpoint_address', '')
    
    # Target only Endpoint 0x03 OUT (The Configuration Pipeline)
    if (ep == '0x03' or ep == '03') and len(hid_data) == 64:
        if hid_data == target_start_hex:
            found_start = True
        
        if found_start:
            config_payloads.append(hid_data)
            if len(config_payloads) == 68:
                break

if len(config_payloads) < 68:
    print(f"❌ Error: Could only find {len(config_payloads)} configuration packets.")
    exit()

print(f"✅ Extracted 68 configuration packets. Ready to flash.")

# --- 2. EXECUTE THE HANDSHAKE & FLASH ---
print("\n🔌 Connecting to Mouse...")
driver.Set_VIDPID(VID, PID)
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

# Step A: Security Unlock (Password from Data.ini)
print("🔓 Unlocking Sequence...")
send_feature("08AACCEE0000001E")
send_feature("0AFC1522000000BD") # Password: FC 15 22
time.sleep(0.01)

# Step B: The Secret Handshake (From json3.json)
print("🔑 Executing Handshake (Watch for LED Blink)...")
send_feature("252B4155F0E0E6EE") # Frame 253
time.sleep(0.01)

# Frame 255/256: Get Confirmation
buf = (ctypes.c_byte * 8)()
driver.GetFeature(buf, 8) 

# Trigger Sequence (Frames 257-269)
triggers = [
    "252BA5FFF0E0E6EE", # Frame 257
    "252BA1FFF0E0E6EE", # Frame 259
    "252BA2FFF0E0E6EE", # Frame 261
    "252BA3FFF0E0E6EE", # Frame 263
    "252BA4FFF0E0E6EE", # Frame 265
    "252BA6FFF0E0E6EE", # Frame 267
    "252BA7FFF0E0E6EE"  # Frame 269
]
for t in triggers:
    send_feature(t)
    time.sleep(0.01)

# Step C: Flash the 68 Configuration Packets
print("💾 LED BLINKED! Flashing the 68 configuration packets...")
success_count = 0
for i, hex_pkt in enumerate(config_payloads):
    payload = bytes.fromhex(hex_pkt)
    # Send 32-byte data to Endpoint 3
    res = driver.WriteUSB((ctypes.c_byte * 32)(*payload), 32)
    if res != 0:
        success_count += 1
    
    # Timing: 30ms gap every 4 packets matches original app behavior
    if (i + 1) % 4 == 0:
        time.sleep(0.03)
    else:
        time.sleep(0.005)

print(f"\n✅ Done! Sent {success_count}/68 configuration packets.")
if success_count == 68:
    print("🎉 Settings Applied! Test your DPI button and buttons.")
else:
    print("⚠️ Warning: Some packets failed to send. Check DLL connectivity.")