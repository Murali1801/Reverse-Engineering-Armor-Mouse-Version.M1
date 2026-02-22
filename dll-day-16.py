import ctypes
import time

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE YOUR HARDWARE HERE)
# =====================================================================

# --- ⚙️ HARDWARE SETTINGS (Flashes directly to the Mouse MCU) ---
POLLING_RATE = 250   # Range: 1000, 500, 250, or 125
KEY_RESPONSE_MS = 12 # Range: 4 to 26 (Debounce)

# --- 💻 WINDOWS OS SETTINGS (Software Level) ---
POINTER_SPEED = 6       # Range: 1 to 11
ENHANCE_PRECISION = False # True or False
DOUBLE_CLICK_MS = 500    # Range: 200 to 900
SCROLL_ONE_PAGE = False  # True or False
SCROLL_LINES = 3         # Range: 1 to 11

# --- 🚀 ADVANCED TUNING (Speed Optimization) ---
# USB_DELAY: Pause between USB packets. Lower is faster, but too low drops packets.
USB_DELAY = 0.005 # Dropped from 0.02 to 0.005 (5ms)

# MCU_WAKE_DELAY: Wait time for the mouse to reboot its RAM. 
# 0.1s was too fast (caused 250Hz bug). 1.0s is safe. Let's try 0.4s.
MCU_WAKE_DELAY = 0.4 

# --- 🎨 DPI SPEEDS & COLORS (Hardware Level) ---
DPI_STAGES = [400, 800, 1200, 2400, 3200, 6200]
DPI_COLORS = [
    "FFFFFF", "00FF00", "0000FF", "FFFF00", "FF8800", "00FFFF"
]

# --- 🕹️ BUTTON MAPPING (Hardware Level - 16 Slots) ---
BUTTONS_BLOCK_1 = [
    "0100F000", "07000300", "0100F200", "0100F400", 
    "0100F300", "0100F100", "00000000", "00000000"
]
BUTTONS_BLOCK_2 = [
    "00000000", "00000000", "00000000", "00000000", 
    "00000000", "00000000", "04000100", "04000200"
]


# =====================================================================
# 2. INPUT VALIDATION & SAFETY CLAMPING
# =====================================================================
def clamp(n, minn, maxn): return max(min(n, maxn), minn)

if POLLING_RATE not in [1000, 500, 250, 125]:
    POLLING_RATE = 1000

KEY_RESPONSE_MS = clamp(KEY_RESPONSE_MS, 4, 26)
POINTER_SPEED = clamp(POINTER_SPEED, 1, 11)
SCROLL_LINES = clamp(SCROLL_LINES, 1, 11)
DOUBLE_CLICK_MS = clamp(DOUBLE_CLICK_MS, 200, 900)


# =====================================================================
# 3. DRIVER ENGINE & SECURITY LOGIC
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
    time.sleep(USB_DELAY) # Optimized USB Delay

def send_data(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 32: data += b'\x00' * (32 - len(data))
    res = driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    print(f"  [Mem] {hex_str[:16]}... | Status: {res}")
    time.sleep(USB_DELAY) # Optimized USB Delay

def build_standard_cmd(byte_list):
    checksum = (255 - sum(byte_list)) & 0xFF 
    byte_list.append(checksum)
    return "".join([f"{b:02X}" for b in byte_list])

def apply_windows_settings():
    print("\n🖥️ Applying Windows OS Mouse Settings...")
    ctypes.windll.user32.SetDoubleClickTime(DOUBLE_CLICK_MS)
    
    if SCROLL_ONE_PAGE:
        scroll_val = -1 
        print(f"  [OS] Scroll Speed set to: One Full Page")
    else:
        scroll_val = SCROLL_LINES
        print(f"  [OS] Scroll Speed set to: {SCROLL_LINES} lines")

    ctypes.windll.user32.SystemParametersInfoW(0x0069, scroll_val, 0, 3)
    
    speed_map = {1:1, 2:2, 3:4, 4:6, 5:8, 6:10, 7:12, 8:14, 9:16, 10:18, 11:20}
    win_speed = speed_map.get(POINTER_SPEED, 10)
    ctypes.windll.user32.SystemParametersInfoW(0x0071, 0, ctypes.c_void_p(win_speed), 3)

    arr = (ctypes.c_int * 3)(0, 0, 0) if not ENHANCE_PRECISION else (ctypes.c_int * 3)(6, 10, 1)
    ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, ctypes.byref(arr), 3)

    print(f"  [OS] Pointer Speed set to: {POINTER_SPEED}/11")


# =====================================================================
# 4. DYNAMIC PAYLOAD COMPILER
# =====================================================================
print("\n🧮 Compiling dynamically calculated commands...")

hz_map = {1000: 0x01, 500: 0x02, 250: 0x04, 125: 0x08}
rate_val = hz_map.get(POLLING_RATE, 0x01)
polling_cmd = build_standard_cmd([0x01, rate_val, 0x00, 0x00, 0x00, 0x00, 0x00])
debounce_cmd = build_standard_cmd([0x04, 0x01, KEY_RESPONSE_MS, 0x00, 0x00, 0x00, 0x00])
move_cmd_hw = build_standard_cmd([0x0E, 0x64, 0x64, 0x00, 0x00, 0x00, 0x00])

flash_prep_sequences = {
    1000: ["272BDDFFE8D57676", "272BD5FFE8ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    500:  ["272BDDFFE8D57676", "272BDDFF00ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    250:  ["272BDDFFE8D57676", "272BADFFD0ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    125:  ["272BDDFFE8D57676", "272B8DFF30ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"]
}
active_prep_sequence = flash_prep_sequences.get(POLLING_RATE, flash_prep_sequences[1000])

color_payload = "".join(DPI_COLORS)
dpi_payload = "".join([f"{int(dpi/100):02X}" for dpi in DPI_STAGES]) + "7C78"
btn1_payload = "".join(BUTTONS_BLOCK_1)
btn2_payload = "".join(BUTTONS_BLOCK_2)


# =====================================================================
# 5. HARDWARE FLASHING SEQUENCE (DMA INJECTION)
# =====================================================================
print("🔌 Opening USB Handles...\n")
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

print("🔓 1. Initializing Hardware Waking...")
send_cmd("2727DDFFF4DD7676") 
send_cmd("252BA5FFF0E0E6EE") 

print(f"\n🧹 2. Preparing Flash Sectors (Injecting {POLLING_RATE}Hz Matrix)...")
for cmd in active_prep_sequence: send_cmd(cmd)

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

print(f"⏳ Waiting {MCU_WAKE_DELAY}s for MCU memory copy to finish...")
time.sleep(MCU_WAKE_DELAY) # Optimized Wait Time

print("\n🛠️ 7. Applying Runtime System Parameters to Active RAM...")
send_cmd(polling_cmd)   
send_cmd(move_cmd_hw)
send_cmd(debounce_cmd)  

apply_windows_settings()
print("\n🎉 SUCCESS! Hardware and OS settings fully updated.")