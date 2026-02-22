import ctypes
import time

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE YOUR HARDWARE HERE)
# =====================================================================

# --- SYSTEM SETTINGS ---
# POLLING_RATE: USB report rate in Hz. (1000 or 125)
POLLING_RATE = 1000

# MOVE_SPEED: Mouse pointer sensitivity multiplier (1 to 200). Default is 100.
MOVE_SPEED = 100 

# KEY_RESPONSE_MS: Hardware debounce time to prevent accidental double-clicks.
# Range: 4 to 100. 12ms in Decimal = 0C in Hex.
KEY_RESPONSE_MS = 12 

# --- DPI SPEEDS & COLORS ---
DPI_STAGES = [400, 800, 1200, 2400, 3200, 6200]
DPI_COLORS = [
    "FFFFFF",  # Stage 1: White
    "00FF00",  # Stage 2: Green
    "0000FF",  # Stage 3: Blue
    "FFFF00",  # Stage 4: Yellow
    "FF8800",  # Stage 5: Orange
    "00FFFF"   # Stage 6: Cyan
]

# --- BUTTON MAPPING (16 Total Slots) ---
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click
    "07000300",  # Slot 2: DPI Cycle 
    "0100F200",  # Slot 3: Middle Click
    "0100F400",  # Slot 4: Forward
    "0100F300",  # Slot 5: Backward
    "0100F100",  # Slot 6: Right Click
    "00000000",  # Slot 7: Button Off
    "00000000"   # Slot 8: Button Off
]

BUTTONS_BLOCK_2 = [
    "00000000", "00000000", "00000000", "00000000", 
    "00000000", "00000000", "04000100", "04000200"
]


# =====================================================================
# 2. DRIVER ENGINE & SECURITY LOGIC
# =====================================================================
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}"); exit()

driver.Set_VIDPID(0x04D9, 0xA09F)

def send_cmd(hex_str):
    data = bytes.fromhex(hex_str)
    res = driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    print(f"  [Cmd] {hex_str} | Status: {res}")
    time.sleep(0.02)

def send_data(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 32: data += b'\x00' * (32 - len(data))
    res = driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    print(f"  [Mem] {hex_str[:16]}... | Status: {res}")
    time.sleep(0.02)

def build_standard_cmd(byte_list):
    checksum = (255 - sum(byte_list)) & 0xFF 
    byte_list.append(checksum)
    return "".join([f"{b:02X}" for b in byte_list])


# =====================================================================
# 3. DYNAMIC PAYLOAD COMPILER
# =====================================================================
print("🧮 Compiling dynamically calculated commands...")

# Runtime RAM Parameters
hz_map = {1000: 0x01, 500: 0x02, 250: 0x04, 125: 0x08}
rate_val = hz_map.get(POLLING_RATE, 0x01)
polling_cmd = build_standard_cmd([0x01, rate_val, 0x00, 0x00, 0x00, 0x00, 0x00])
move_cmd = build_standard_cmd([0x0E, MOVE_SPEED, MOVE_SPEED, 0x00, 0x00, 0x00, 0x00])
debounce_cmd = build_standard_cmd([0x04, 0x01, KEY_RESPONSE_MS, 0x00, 0x00, 0x00, 0x00])

# --- THE FIX: DYNAMIC FLASH POLLING COMMAND ---
if POLLING_RATE == 125:
    flash_polling_cmd = "272B8DFF30ED7676"  # 125Hz Flash Burn
else:
    flash_polling_cmd = "272BD5FFE8ED7676"  # 1000Hz Flash Burn Default

color_payload = "".join(DPI_COLORS)
dpi_payload = "".join([f"{int(dpi/100):02X}" for dpi in DPI_STAGES]) + "7C78"
btn1_payload = "".join(BUTTONS_BLOCK_1)
btn2_payload = "".join(BUTTONS_BLOCK_2)


# =====================================================================
# 4. HARDWARE FLASHING SEQUENCE (DMA INJECTION)
# =====================================================================
print("🔌 Opening USB Handles...\n")
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

print("🔓 1. Initializing Hardware Waking...")
send_cmd("2727DDFFF4DD7676") 
send_cmd("252BA5FFF0E0E6EE") 

print("\n🧹 2. Preparing Flash Sectors...")
send_cmd("272BDDFFE8D57676")
send_cmd(flash_polling_cmd) # THE FIX: Dynamically burning the correct Hz to Flash!
send_cmd("272B6DFF001D7676")
send_cmd("272B9D0498457676")
send_cmd("272B5DFFD0524E8E")

print("\n🎨 3. Flashing LED Colors (Dual Sector Write)...")
send_cmd("272A85FFF0657636") 
send_data(color_payload)     
send_cmd("272A8DFFE8657636") 
send_data(color_payload)     

print("\n⚡ 4. Flashing DPI Profiles...")
send_cmd("272BFDFFE06D76B6") 
send_data(dpi_payload)       

print("\n⚙️ 5. Flashing Button Mappings...")
send_cmd("272D5DFFE8557876") 
send_data(btn1_payload)      
send_cmd("272D25FF00557876") 
send_data(btn2_payload)      

print("\n🏁 6. Locking Configuration (Flash to RAM Reload)...")
send_cmd("272BFDFFF86576D6") 
send_data("FF000000000000000000000000000000") 

time.sleep(0.1) 

print("\n🛠️ 7. Applying Runtime System Parameters to Active RAM...")
send_cmd(polling_cmd)   
send_cmd(move_cmd)      
send_cmd(debounce_cmd)  

print("\n🎉 SUCCESS! Hardware fully updated and parameters locked.")