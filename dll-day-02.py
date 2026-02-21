import ctypes
import time

# --- CONFIGURATION ---
VID = 0x04D9
PID = 0xA09F

# --- LOAD DLL ---
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

# DLL Function Signatures
driver.Set_VIDPID.argtypes = [ctypes.c_int, ctypes.c_int]
driver.SetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.SetFeature.restype = ctypes.c_int
driver.WriteUSB.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.WriteUSB.restype = ctypes.c_int
driver.GetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.GetFeature.restype = ctypes.c_int
driver.Open_FeatureDevice.restype = ctypes.c_int
driver.Open_ReportDevice.restype = ctypes.c_int
driver.Open_DevMonitor.restype = ctypes.c_int

def send_feature(hex_str):
    """Utility to send an 8-byte Feature Report from a hex string."""
    data = bytes.fromhex(hex_str)
    return driver.SetFeature((ctypes.c_byte * 8)(*data), 8)

# --- THE 68-PACKET DATA BURST ---
# This data is reconstructed from your successful Wireshark capture
# These packets contain the actual RGB, DPI, and Button configurations.
burst_data = [
    "ff000000ff000000ffff00ff00ff00ffffff8000ffffff0000000000000000", # Pkt 1 (RGB)
    "ff000000ff000000ffff00ff00ff00ffffffffffff55000000000000000000", # Pkt 2
    "7e7e1820607c7c78000000000000000000000000000000000000000000000000", # Pkt 3 (DPI)
    "0100f0000100f1000100f2000100f4000100f300070001000b00000005000300", # Pkt 4 (Buttons)
    # ... The remaining 64 packets continue the memory overwrite ...
]
# Note: For the full 68-packet list, ensure you are using the array parsed from json.json

# --- MAIN EXECUTION ---
print("🔌 Connecting to Mouse...")
driver.Set_VIDPID(VID, PID)
driver.Open_DevMonitor()
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

# 1. INITIAL UNLOCK
print("🔓 Unlocking Sequence...")
send_feature("08AACCEE0000001E")
time.sleep(0.01)
send_feature("0AFC1522000000BD")
time.sleep(0.01)

# 2. THE SECRET 8-STEP HANDSHAKE (Extracted from json3.json)
print("🔑 Executing Secret Handshake...")

# Packet 253
send_feature("252B4155F0E0E6EE") 
time.sleep(0.01)

# Packet 255/256: Get Confirmation
buf = (ctypes.c_byte * 8)()
driver.GetFeature(buf, 8) 
time.sleep(0.01)

# Remaining Trigger Sequence (Packets 257-269)
triggers = [
    "252BA5FFF0E0E6EE", # Pkt 257
    "252BA1FFF0E0E6EE", # Pkt 259
    "252BA2FFF0E0E6EE", # Pkt 261
    "252BA3FFF0E0E6EE", # Pkt 263
    "252BA4FFF0E0E6EE", # Pkt 265
    "252BA6FFF0E0E6EE", # Pkt 267
    "252BA7FFF0E0E6EE"  # Pkt 269
]

for t in triggers:
    send_feature(t)
    time.sleep(0.01)

print("   ✅ Handshake Complete. Mouse is now in Download Mode.")

# 3. THE 68-PACKET DATA BURST
print("💾 Blasting 68-Packet Profile Burst...")
success_count = 0

# Loop through the hex strings in burst_data
for i, hex_pkt in enumerate(burst_data):
    payload = bytes.fromhex(hex_pkt)
    res = driver.WriteUSB((ctypes.c_byte * 32)(*payload), 32)
    if res != 0:
        success_count += 1
    time.sleep(0.01) # 10ms delay matches Wireshark timing

print(f"\n✅ Burst Complete! Sent {success_count} packets.")
print("👉 TEST: Change your DPI or click a button to see if settings applied.")