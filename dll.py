"""
Armor Gaming Mouse Custom Driver
Reverse-Engineered by Custom Protocol Injection
MCU: Holtek HT68FB571
"""

import ctypes
import time

# Start the execution stopwatch
start_time = time.perf_counter()

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE YOUR MOUSE HERE)
# =====================================================================

# --- ⚙️ HARDWARE SETTINGS (Flashes directly to the Mouse MCU RAM/Flash) ---

# POLLING_RATE: USB report rate in Hz (How often the mouse talks to the PC).
# Valid Options: 1000 (1ms), 500 (2ms), 250 (4ms), or 125 (8ms).
POLLING_RATE = 250 

# KEY_RESPONSE_MS: Hardware switch debounce time. Prevents accidental double clicks.
# Range: 4ms (Hyper-fast, prone to double clicks) to 26ms (Safe/Slow).
KEY_RESPONSE_MS = 12 

# --- 💻 WINDOWS OS SETTINGS (Software Level Hooks) ---

# POINTER_SPEED: Windows Cursor Speed. Matches the official software's 1-11 slider.
# Windows default is 6. Higher numbers move the cursor further per physical inch.
POINTER_SPEED = 6        

# ENHANCE_PRECISION: Windows Mouse Acceleration. True = ON, False = OFF.
ENHANCE_PRECISION = False 

# DOUBLE_CLICK_SPEED: Matches the UI slider from 0 to 10.
# 0 = Slowest (~900ms window). 10 = Fastest (~200ms window). Windows default is 5.
DOUBLE_CLICK_SPEED = 5   

# SCROLL_ONE_PAGE: If True, scrolling one notch jumps an entire screen height.
SCROLL_ONE_PAGE = False  

# SCROLL_LINES: Number of text lines to scroll per physical wheel notch.
# Range: 1 to 11. Windows default is usually 3.
SCROLL_LINES = 3         


# --- 🚀 ADVANCED TUNING (Communication Speed Optimization) ---

# USB_DELAY: Time to pause between sending USB packets (in seconds).
# 0.005s (5ms) is incredibly fast but stable for modern USB HID protocols.
USB_DELAY = 0.005 

# MCU_WAKE_DELAY: Wait time for the mouse to copy its Flash memory to its active RAM.
# If this is too low (e.g., 0.1s), the RAM settings get overwritten by the Flash memory.
MCU_WAKE_DELAY = 0.4 


# --- 🎨 DPI SPEEDS & COLORS (Hardware Flash Memory) ---

# DPI_STAGES: The 6 sensor resolution steps. Must be multiples of 100. Max 6200.
DPI_STAGES = [400, 800, 1200, 2400, 3200, 6200]

# DPI_COLORS: The RGB LED Hex codes tied to each DPI stage above.
DPI_COLORS = [
    "FFFFFF", # Stage 1: White
    "00FF00", # Stage 2: Green
    "0000FF", # Stage 3: Blue
    "FFFF00", # Stage 4: Yellow
    "FF8800", # Stage 5: Orange
    "00FFFF"  # Stage 6: Cyan
]


# --- 🕹️ BUTTON MAPPING (Hardware Flash Memory - 16 Slots) ---
# Format: Byte 1 = Key Mode (01 = Mouse Button). Byte 3 = Key Code (F0 = Left Click)
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click
    "07000300",  # Slot 2: DPI Cycle (Mode 07 = DPI Switch, Code 03 = Loop)
    "0100F200",  # Slot 3: Middle Click
    "0100F400",  # Slot 4: Forward (Button 5)
    "0100F300",  # Slot 5: Backward (Button 4)
    "0100F100",  # Slot 6: Right Click
    "00000000",  # Slot 7: Unassigned / Disabled
    "00000000"   # Slot 8: Unassigned / Disabled
]

BUTTONS_BLOCK_2 = [
    "00000000",  # Slot 9: Unassigned
    "00000000",  # Slot 10: Unassigned
    "00000000",  # Slot 11: Unassigned
    "00000000",  # Slot 12: Unassigned
    "00000000",  # Slot 13: Unassigned
    "00000000",  # Slot 14: Unassigned
    "04000100",  # Slot 15: Scroll Wheel Up (Mode 04 = Scroll)
    "04000200"   # Slot 16: Scroll Wheel Down (Mode 04 = Scroll)
]


# =====================================================================
# 2. INPUT VALIDATION & SAFETY CLAMPING
# =====================================================================
# Ensures user inputs do not exceed the boundaries allowed by the OS/Hardware
def clamp(n, minn, maxn): return max(min(n, maxn), minn)

# Force polling rate to standard USB intervals
if POLLING_RATE not in [1000, 500, 250, 125]:
    POLLING_RATE = 1000

# Clamp all other values to their exact UI slider boundaries
KEY_RESPONSE_MS = clamp(KEY_RESPONSE_MS, 4, 26)
POINTER_SPEED = clamp(POINTER_SPEED, 1, 11)
SCROLL_LINES = clamp(SCROLL_LINES, 1, 11)
DOUBLE_CLICK_SPEED = clamp(DOUBLE_CLICK_SPEED, 0, 10) 


# =====================================================================
# 3. DRIVER ENGINE & OS HOOKS
# =====================================================================
try:
    # Loads the manufacturer's C++ library to communicate with the USB stack
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}"); exit()

# Target the specific Holtek MCU hardware ID (Vendor ID: 04D9, Product ID: A09F)
driver.Set_VIDPID(0x04D9, 0xA09F)

def send_cmd(hex_str):
    """Sends 8-byte Feature Reports (Used for settings and memory addresses)"""
    data = bytes.fromhex(hex_str)
    res = driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    print(f"  [Cmd] {hex_str} | Status: {res}")
    time.sleep(USB_DELAY) 

def send_data(hex_str):
    """Sends 32-byte Output Reports (Used for injecting long custom payloads)"""
    data = bytes.fromhex(hex_str)
    # Pads the data with zeros if it doesn't fill the full 32-byte buffer
    if len(data) < 32: data += b'\x00' * (32 - len(data))
    res = driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    print(f"  [Mem] {hex_str[:16]}... | Status: {res}")
    time.sleep(USB_DELAY) 

def build_standard_cmd(byte_list):
    """Calculates the Holtek C++ Checksum: Checksum = 255 - Sum(Bytes 0-6)"""
    checksum = (255 - sum(byte_list)) & 0xFF 
    byte_list.append(checksum)
    return "".join([f"{b:02X}" for b in byte_list])

def apply_windows_settings():
    """Hooks into the Windows User32 API to change OS-level mouse configurations"""
    print("\n🖥️ Applying Windows OS Mouse Settings...")
    
    # 1. Double Click Speed
    # Maps the 0-10 slider to Windows Milliseconds (900ms down to 200ms)
    calc_double_click_ms = 900 - (DOUBLE_CLICK_SPEED * 70)
    ctypes.windll.user32.SetDoubleClickTime(calc_double_click_ms)
    
    # 2. Scroll Speed (SPI_SETWHEELSCROLLLINES = 0x0069)
    if SCROLL_ONE_PAGE:
        scroll_val = -1 # -1 tells Windows to use "Page Scroll" mode
        print(f"  [OS] Scroll Speed set to: One Full Page")
    else:
        scroll_val = SCROLL_LINES
        print(f"  [OS] Scroll Speed set to: {SCROLL_LINES} lines")
    # '3' at the end broadcasts the change to all open applications instantly
    ctypes.windll.user32.SystemParametersInfoW(0x0069, scroll_val, 0, 3)
    
    # 3. Pointer Speed (SPI_SETMOUSESPEED = 0x0071)
    # Maps the UI 1-11 slider to the Windows internal 1-20 scale
    speed_map = {1:1, 2:2, 3:4, 4:6, 5:8, 6:10, 7:12, 8:14, 9:16, 10:18, 11:20}
    win_speed = speed_map.get(POINTER_SPEED, 10)
    ctypes.windll.user32.SystemParametersInfoW(0x0071, 0, ctypes.c_void_p(win_speed), 3)

    # 4. Enhance Pointer Precision / Acceleration (SPI_SETMOUSE = 0x0004)
    # Requires a specific 3-integer array for Windows acceleration curves
    arr = (ctypes.c_int * 3)(0, 0, 0) if not ENHANCE_PRECISION else (ctypes.c_int * 3)(6, 10, 1)
    ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, ctypes.byref(arr), 3)

    print(f"  [OS] Pointer Speed set to: {POINTER_SPEED}/11")
    print(f"  [OS] Double Click Speed set to: {DOUBLE_CLICK_SPEED}/10 ({calc_double_click_ms}ms)")


# =====================================================================
# 4. DYNAMIC PAYLOAD COMPILER
# =====================================================================
print("\n🧮 Compiling dynamically calculated commands...")

# Runtime RAM Parameters (Volatile Memory - Lost on Reboot)
# Polling Rate (Command 01H) 
hz_map = {1000: 0x01, 500: 0x02, 250: 0x04, 125: 0x08}
rate_val = hz_map.get(POLLING_RATE, 0x01)
polling_cmd = build_standard_cmd([0x01, rate_val, 0x00, 0x00, 0x00, 0x00, 0x00])

# Hardware Debounce (Command 04H - Sensor Lift/Debounce Register)
debounce_cmd = build_standard_cmd([0x04, 0x01, KEY_RESPONSE_MS, 0x00, 0x00, 0x00, 0x00])

# Hardware X/Y Sensitivity (Command 0EH)
# We default to 100% (0x64) hardware scale because Windows OS controls the actual speed.
move_cmd_hw = build_standard_cmd([0x0E, 0x64, 0x64, 0x00, 0x00, 0x00, 0x00])

# --- DYNAMIC FLASH STATE MATRIX ---
# These specific memory sectors dictacte the permanent polling rate burned into the MCU.
# Discovered by clean-room reverse engineering the 27H commands.
flash_prep_sequences = {
    1000: ["272BDDFFE8D57676", "272BD5FFE8ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    500:  ["272BDDFFE8D57676", "272BDDFF00ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    250:  ["272BDDFFE8D57676", "272BADFFD0ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    125:  ["272BDDFFE8D57676", "272B8DFF30ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"]
}
active_prep_sequence = flash_prep_sequences.get(POLLING_RATE, flash_prep_sequences[1000])

# Concatenate long arrays into contiguous 32-byte hexadecimal memory strings
color_payload = "".join(DPI_COLORS)
# Adds the static 7C78 suffix to the end of the DPI byte array
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
# Official wake command handshake
send_cmd("2727DDFFF4DD7676") 
# Security bypass key to unlock the memory sectors
send_cmd("252BA5FFF0E0E6EE") 

print(f"\n🧹 2. Preparing Flash Sectors (Injecting {POLLING_RATE}Hz Matrix)...")
for cmd in active_prep_sequence: send_cmd(cmd)

print("\n🎨 3. Flashing LED Colors (Dual Sector Write)...")
# Sector address for RGB LED states
send_cmd("272A85FFF0657636") 
send_data(color_payload)     
send_cmd("272A8DFFE8657636") 
send_data(color_payload)     

print("\n⚡ 4. Flashing DPI Profiles...")
# Sector address for sensor DPI stages
send_cmd("272BFDFFE06D76B6") 
send_data(dpi_payload)       

print("\n⚙️ 5. Flashing Button Mappings...")
# Sector address for the 16 button mappings (Split across two sectors)
send_cmd("272D5DFFE8557876") 
send_data(btn1_payload)      
send_cmd("272D25FF00557876") 
send_data(btn2_payload)      

print("\n🏁 6. Locking Configuration (Flash to RAM Reload)...")
# Triggers the microchip to seal the flash memory and copy it to active RAM
send_cmd("272BFDFFF86576D6") 
send_data("FF000000000000000000000000000000") 

# Required delay to prevent Race Condition: We must wait for the MCU to finish 
# copying its Flash memory over its RAM before we send the active RAM commands.
print(f"⏳ Waiting {MCU_WAKE_DELAY}s for MCU memory copy to finish...")
time.sleep(MCU_WAKE_DELAY) 

print("\n🛠️ 7. Applying Runtime System Parameters to Active RAM...")
# Flashes volatile settings. If the mouse is unplugged, it loses these and 
# re-reads defaults from its flash memory.
send_cmd(polling_cmd)   
send_cmd(move_cmd_hw)
send_cmd(debounce_cmd)  

# Hooks into Windows OS to finish the software-side configuration
apply_windows_settings()
print("\n🎉 SUCCESS! Hardware and OS settings fully updated.")

# Stop the timer and print the performance result
end_time = time.perf_counter()
total_time = end_time - start_time
print(f"⏱️ Total execution time: {total_time:.2f} seconds\n")