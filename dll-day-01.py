import ctypes
import time

# --- CONFIGURATION ---
VID = 0x04D9
PID = 0xA09F
# Command: Stop Macros [08, AA, CC, EE, 00, 00, 00]
CMD_STOP = [0x08, 0xAA, 0xCC, 0xEE, 0x00, 0x00, 0x00]
# Command: Unlock [0A, FC, 15, 22, 00, 00, 00]
CMD_UNLOCK = [0x0A, 0xFC, 0x15, 0x22, 0x00, 0x00, 0x00]
# Command: Red LED [0C, FF, 00, 00, 00, 00, 00]
CMD_RED = [0x0C, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00]

# --- LOAD DLL ---
driver = ctypes.CDLL("./MSDriver.dll")
driver.Set_VIDPID.argtypes = [ctypes.c_int, ctypes.c_int]
driver.SetFeature.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.SetFeature.restype = ctypes.c_int
driver.WriteUSB.argtypes = [ctypes.POINTER(ctypes.c_byte), ctypes.c_int]
driver.WriteUSB.restype = ctypes.c_int
driver.Open_FeatureDevice.restype = ctypes.c_int
driver.Open_ReportDevice.restype = ctypes.c_int
driver.Open_DevMonitor.restype = ctypes.c_int

# --- CHECKSUM & PADDING ---
def prepare_packet(base_bytes, total_size=32):
    # 1. Start with base bytes
    packet = base_bytes[:]
    
    # 2. Calculate Checksum (Sum of first 8 bytes must be 255)
    # The checksum always goes into Byte 7 (the 8th byte)
    current_sum = sum(packet[:7])
    checksum = (255 - (current_sum % 256))
    if checksum < 0: checksum += 256
    
    if len(packet) < 8:
        packet.append(checksum)
    else:
        packet[7] = checksum
        
    # 3. Pad to Target Size (Critical Step!)
    padding_needed = total_size - len(packet)
    packet += [0x00] * padding_needed
    
    return packet

def send_command(name, cmd_bytes):
    print(f"\n📨 Sending {name}...")
    
    # We will try both Standard (32) and ReportID (33) sizes
    sizes_to_try = [32, 64] 
    
    for size in sizes_to_try:
        # Prepare 32/64 byte packet
        pkt = prepare_packet(cmd_bytes, total_size=size)
        arr = (ctypes.c_byte * size)(*pkt)
        
        # Try SetFeature (Preferred)
        print(f"   👉 SetFeature ({size} bytes): ", end="")
        if driver.SetFeature(arr, size) != 0:
            print("✅ SUCCESS!")
            return True
        print("Failed.")
        
        # Try WriteUSB (Backup)
        print(f"   👉 WriteUSB   ({size} bytes): ", end="")
        if driver.WriteUSB(arr, size) != 0:
            print("✅ SUCCESS!")
            return True
        print("Failed.")
    
    return False

# --- MAIN EXECUTION ---
print(f"🔌 Connecting to VID={hex(VID)} PID={hex(PID)}...")
driver.Set_VIDPID(VID, PID)
driver.Open_DevMonitor()

# Open BOTH handles just in case
h_feat = driver.Open_FeatureDevice()
h_rep  = driver.Open_ReportDevice()
print(f"   Handles -> Feature: {h_feat} | Report: {h_rep}")

if h_feat != 0 or h_rep != 0:
    # 1. STOP MACROS
    if send_command("Stop Macros", CMD_STOP):
        time.sleep(0.1)
        
        # 2. UNLOCK
        if send_command("Unlock Device", CMD_UNLOCK):
            time.sleep(0.1)
            
            # 3. RED LED
            send_command("Set LED Red", CMD_RED)
            print("\n🔴 CHECK YOUR MOUSE! IS IT RED?")
        else:
            print("❌ Unlock Failed. (But Stop Macros worked!)")
    else:
        print("❌ Stop Macros Failed.")
else:
    print("❌ Could not open any device handle. (Is 'Armor' app running?)")