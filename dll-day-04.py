import ctypes
import time
import json

# --- CONFIGURATION ---
VID = 0x04D9
PID = 0xA09F

# --- LOAD DLL ---
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

driver.Set_VIDPID.argtypes = [ctypes.c_int, ctypes.c_int]
driver.SetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.SetFeature.restype = ctypes.c_int
driver.WriteUSB.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.WriteUSB.restype = ctypes.c_int
driver.GetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.GetFeature.restype = ctypes.c_int

def send_feature(hex_str):
    data = bytes.fromhex(hex_str)
    return driver.SetFeature((ctypes.c_byte * 8)(*data), 8)

# --- 1. EXTRACT DATA ---
print("📂 Extracting configuration from json.json...")
try:
    with open('json.json', 'r', encoding='utf-8') as f:
        capture_data = json.load(f)
    
    target_start = "ff000000ff000000ffffff00ff00ff00ffffff8000ffffff0000000000000000"
    config_payloads = []
    found = False
    for pkt in capture_data:
        hid = pkt.get('_source', {}).get('layers', {}).get('usbhid.data', '').replace(':', '')
        if len(hid) == 64:
            if hid == target_start: found = True
            if found:
                config_payloads.append(hid)
                if len(config_payloads) == 68: break
except:
    print("❌ Error processing json.json")
    exit()

# --- 2. EXECUTION ---
print("\n🔌 Connecting...")
driver.Set_VIDPID(VID, PID)
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

# STEP A: THE RESET (Clear any old stuck states)
print("🧹 Resetting Mouse State...")
send_feature("08AACCEE0000001E") # The standard STOP command
time.sleep(0.05)

# STEP B: THE HANDSHAKE
print("🔓 Unlocking & Handshaking...")
send_feature("0AFC1522000000BD") # Password
time.sleep(0.01)
send_feature("252B4155F0E0E6EE") # Handshake Start
time.sleep(0.02)

buf = (ctypes.c_byte * 8)()
driver.GetFeature(buf, 8) # Sync

triggers = ["252BA5FFF0E0E6EE", "252BA1FFF0E0E6EE", "252BA2FFF0E0E6EE", 
            "252BA3FFF0E0E6EE", "252BA4FFF0E0E6EE", "252BA6FFF0E0E6EE", "252BA7FFF0E0E6EE"]
for t in triggers:
    send_feature(t)
    time.sleep(0.01)

# STEP C: THE DATA BURST
print("💾 LED BLINKED! Sending 68 packets...")
success = 0
for i, hex_pkt in enumerate(config_payloads):
    payload = bytes.fromhex(hex_pkt)
    if driver.WriteUSB((ctypes.c_byte * 32)(*payload), 32) != 0:
        success += 1
    if (i + 1) % 4 == 0:
        time.sleep(0.03) # Write delay
    else:
        time.sleep(0.005)

# STEP D: THE COMMIT (This is what was missing!)
print("🔒 Committing changes and locking memory...")
send_feature("08AACCEE0000001E") # Re-send STOP to save EEPROM
time.sleep(0.1)

print(f"\n✅ Done! Sent {success}/68 packets.")
print("👉 TEST NOW: Does it blink every time you run the script?")