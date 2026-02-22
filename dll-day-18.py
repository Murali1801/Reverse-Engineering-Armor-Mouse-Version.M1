"""
Armor Gaming Mouse Custom Driver (Ultimate Documented Edition)
MCU: Holtek HT68FB571
Author: Custom Reverse Engineering

This script bypasses the manufacturer's standard protocol and uses 
undocumented Direct Memory Access (DMA) commands to forcefully rewrite 
the mouse's physical silicon memory (EEPROM).
"""

import ctypes
import time

# Start the execution stopwatch to measure script performance
start_time = time.perf_counter()

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE YOUR MOUSE HERE)
# =====================================================================

# --- ⚙️ HARDWARE SETTINGS (Flashes directly to the Mouse MCU RAM/Flash) ---

# POLLING_RATE: USB report rate in Hz (How often the mouse updates the PC).
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


# --- 🚀 ADVANCED STABILITY TUNING ---

# USB_DELAY: Time to pause between sending USB packets (in seconds).
# 0.01s (10ms) ensures the USB buffer never drops packets during large memory transfers.
USB_DELAY = 0.01      


# =====================================================================
# 2. MACRO ENGINE & DEFINITIONS
# =====================================================================
def compile_macro(actions, repeat=1):
    """
    Compiles human-readable actions into an EXACT 128-byte hardware payload.
    The Holtek MCU expects exactly 128 bytes (4 chunks of 32 bytes) per macro. 
    If we send less, the USB Endpoint stalls and the mouse crashes.
    """
    # Bytes 1 & 2: How many times the hardware should repeat the macro.
    payload = [(repeat >> 8) & 0xFF, repeat & 0xFF] 
    
    # USB HID Key Dictionary (Hex codes for physical keys)
    keys = {
        "A": 0x04, "B": 0x05, "C": 0x06, 
        "ENTER": 0x28, "SPACE": 0x2C, "LCLICK": 0xF0
    }
    
    for state, key, delay_ms in actions:
        # The Attribute Byte dictates the action type and the delay time.
        # Bit 7 (0x80) = Release Key. Bit 7 (0x00) = Press Key.
        # Bits 0-6 = Delay before the next action (measured in 10ms steps).
        delay_steps = min(127, delay_ms // 10) 
        attr = delay_steps | (0x80 if state.upper() == "RELEASE" else 0x00)
        
        # Append the Attribute Byte and the Key Code Byte
        payload.extend([attr, keys.get(key.upper(), 0x00)])
        
    # CRITICAL FIX: Pad the remaining macro space with zeros until it reaches EXACTLY 128 bytes.
    # This prevents the MCU from waiting indefinitely for missing data chunks.
    while len(payload) < 128: 
        payload.append(0x00)
        
    # Convert the byte array into a continuous hexadecimal string
    return "".join([f"{b:02X}" for b in payload])

# --- DEFINING YOUR CUSTOM MACRO ---
# Format: ("PRESS" or "RELEASE", "KEY", Delay_Before_Next_Action_in_MS)
# This macro Types 'A', 'B', and clicks the Left Mouse Button, repeating 3 times.
my_custom_macro = compile_macro([
    ("PRESS", "A", 10),       # Press A, wait 10ms
    ("RELEASE", "A", 10),     # Release A, wait 10ms
    ("PRESS", "B", 10),       # Press B, wait 10ms
    ("RELEASE", "B", 10),     # Release B, wait 10ms
    ("PRESS", "LCLICK", 10),  # Press Left Mouse Button, wait 10ms
    ("RELEASE", "LCLICK", 10) # Release Left Mouse Button, end of sequence.
], repeat=3) 


# =====================================================================
# 3. HARDWARE PAYLOADS (COLORS, DPI, BUTTONS)
# =====================================================================

# --- 🎨 DPI SPEEDS & COLORS (Hardware Flash Memory) ---
# DPI_STAGES: The 6 sensor resolution steps. Must be multiples of 100. Max 6200.
DPI_STAGES = [
    400,  # Stage 1
    800,  # Stage 2
    1200, # Stage 3
    2400, # Stage 4
    3200, # Stage 5
    6200  # Stage 6
]

# DPI_COLORS: The RGB LED Hex codes tied to each DPI stage above (Format: RRGGBB)
DPI_COLORS = [
    "FFFFFF", # Stage 1 (400 DPI): White
    "00FF00", # Stage 2 (800 DPI): Green
    "0000FF", # Stage 3 (1200 DPI): Blue
    "FFFF00", # Stage 4 (2400 DPI): Yellow
    "FF8800", # Stage 5 (3200 DPI): Orange
    "00FFFF"  # Stage 6 (6200 DPI): Cyan
]


# --- 🕹️ BUTTON MAPPING (Hardware Flash Memory - 16 Slots) ---
# Format: Byte 1 = Key Mode. Byte 3 = Key Code.
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click (Mode 01 = Mouse Button, Code F0 = L-Click)
    "07000300",  # Slot 2: DPI Cycle (Mode 07 = DPI Switch, Code 03 = Loop)
    "0100F200",  # Slot 3: Middle Click (Mode 01 = Mouse Button, Code F2 = M-Click)
    
    # 09 = Macro Mode. 00 = Normal Type. 01 = Macro ID #1. 00 = Length
    "09000100",  # Slot 4: Forward Button -> Triggers Custom Macro #1!
    
    "0100F300",  # Slot 5: Backward (Mode 01 = Mouse Button, Code F3 = B4)
    "0100F100",  # Slot 6: Right Click (Mode 01 = Mouse Button, Code F1 = R-Click)
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
    "04000100",  # Slot 15: Scroll Wheel Up (Mode 04 = Scroll, Code 01 = Up)
    "04000200"   # Slot 16: Scroll Wheel Down (Mode 04 = Scroll, Code 02 = Down)
]


# =====================================================================
# 4. DRIVER ENGINE & OS HOOKS
# =====================================================================
try:
    # Load the manufacturer's C++ library to communicate with the USB stack
    driver = ctypes.CDLL("./MSDriver.dll")
    # Target the specific Holtek MCU hardware ID (Vendor ID: 04D9, Product ID: A09F)
    driver.Set_VIDPID(0x04D9, 0xA09F)
except Exception as e:
    print(f"❌ DLL Load Failed: {e}"); exit()

def send_cmd(hex_str):
    """Sends 8-byte Feature Reports (Used for setting memory addresses and triggers)"""
    driver.SetFeature((ctypes.c_byte * 8)(*bytes.fromhex(hex_str)), 8)
    print(f"  [Cmd] {hex_str}")
    time.sleep(USB_DELAY) 

def send_data(hex_str):
    """Sends 32-byte Output Reports (Used for injecting long custom payloads)"""
    data = bytes.fromhex(hex_str)
    # Pads the data with zeros if it doesn't fill the full 32-byte USB buffer
    if len(data) < 32: data += b'\x00' * (32 - len(data))
    driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    print(f"  [Mem] {hex_str[:16]}...")
    time.sleep(USB_DELAY)

def build_cmd(byte_list):
    """Calculates the Holtek C++ Checksum: Checksum = 255 - Sum(Bytes 0-6)"""
    byte_list.append((255 - sum(byte_list)) & 0xFF)
    return "".join([f"{b:02X}" for b in byte_list])

def apply_os_settings():
    """Hooks into the Windows User32 API to change OS-level mouse configurations"""
    print("\n🖥️ Applying Windows OS Mouse Settings...")
    
    # Map Double Click Speed: 0-10 slider mapped down to 900ms - 200ms
    ctypes.windll.user32.SetDoubleClickTime(900 - (DOUBLE_CLICK_SPEED * 70))
    
    # Map Scroll Speed (SPI_SETWHEELSCROLLLINES = 0x0069)
    # -1 tells Windows to use "Page Scroll" mode
    ctypes.windll.user32.SystemParametersInfoW(0x0069, -1 if SCROLL_ONE_PAGE else SCROLL_LINES, 0, 3)
    
    # Map Pointer Speed (SPI_SETMOUSESPEED = 0x0071)
    # Maps the UI 1-11 slider to the Windows internal 1-20 scale
    speed_map = {1:1, 2:2, 3:4, 4:6, 5:8, 6:10, 7:12, 8:14, 9:16, 10:18, 11:20}
    ctypes.windll.user32.SystemParametersInfoW(0x0071, 0, ctypes.c_void_p(speed_map.get(POINTER_SPEED, 10)), 3)

    # Windows Enhance Pointer Precision (SPI_SETMOUSE = 0x0004)
    arr = (ctypes.c_int * 3)(0, 0, 0) if not ENHANCE_PRECISION else (ctypes.c_int * 3)(6, 10, 1)
    ctypes.windll.user32.SystemParametersInfoW(0x0004, 0, ctypes.byref(arr), 3)


# =====================================================================
# 5. EXECUTION SEQUENCE (DMA INJECTION)
# =====================================================================
print("🔌 Opening USB Handles...\n")
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

# CRITICAL FIX 1: We MUST stop the macro engine before unlocking secrecy memory!
# If the hardware is ready to fire a macro while we try to lock the flash, it causes a collision.
# Command 08H: Stop Macro Sending
print("🛑 0. Halting Macro Engine...")
send_cmd(build_cmd([0x08, 0xAA, 0xCC, 0xEE, 0x00, 0x00, 0x00]))

print("\n🔓 1. Handshake & Secrecy Unlock...")
send_cmd("2727DDFFF4DD7676") # Undocumented Official Wake Command Handshake
send_cmd("252BA5FFF0E0E6EE") # Security bypass key to unlock the memory sectors

print(f"\n🧹 2. Preparing Flash Sectors (Injecting {POLLING_RATE}Hz Matrix)...")
# Undocumented DMA sequences. These specific memory sectors dictate the 
# permanent polling rate burned into the MCU. Discovered via clean room dumps.
prep = {
    1000: ["272BDDFFE8D57676", "272BD5FFE8ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    500:  ["272BDDFFE8D57676", "272BDDFF00ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    250:  ["272BDDFFE8D57676", "272BADFFD0ED7676", "272B75FFF81D7676", "272B9D0498457676", "272B5DFFD0524E8E"],
    125:  ["272BDDFFE8D57676", "272B8DFF30ED7676", "272B6DFF001D7676", "272B9D0498457676", "272B5DFFD0524E8E"]
}
for cmd in prep.get(POLLING_RATE): send_cmd(cmd)

print("\n🎨 3. Flashing Colors & DPI...")
# 272A85: DMA Sector address for RGB LED states
send_cmd("272A85FFF0657636") 
send_data("".join(DPI_COLORS))
# 272A8D: Secondary DMA Sector address for RGB LED states (Dual Write)
send_cmd("272A8DFFE8657636") 
send_data("".join(DPI_COLORS))

# 272BFD: DMA Sector address for Sensor DPI stages.
# The 7C78 suffix is an undocumented static hardware terminator required by the sensor.
send_cmd("272BFDFFE06D76B6") 
send_data("".join([f"{int(d/100):02X}" for d in DPI_STAGES]) + "7C78")

print("\n⚙️ 4. Flashing Button Mappings...")
# 272D5D: DMA Sector address for the first 8 button mappings
send_cmd("272D5DFFE8557876") 
send_data("".join(BUTTONS_BLOCK_1))
# 272D25: DMA Sector address for the final 8 button mappings
send_cmd("272D25FF00557876") 
send_data("".join(BUTTONS_BLOCK_2))

print("\n🤖 5. Flashing Hardware Macros (DMA Injection)...")
# 272725: Undocumented Macro Slot 1 Flash Command (Bypasses standard 13H Protocol)
send_cmd("272725FFE85D7A76") 

# Send EXACTLY 128 bytes (4 full 32-byte chunks) to prevent USB Endpoint stalling!
send_data(my_custom_macro[0:64])    # Chunk 1 (Bytes 1-32)
send_data(my_custom_macro[64:128])  # Chunk 2 (Bytes 33-64)
send_data(my_custom_macro[128:192]) # Chunk 3 (Bytes 65-96)
send_data(my_custom_macro[192:256]) # Chunk 4 (Bytes 97-128)

print("\n🏁 6. Commit EEPROM & Soft-Reboot...")
# Triggers the microchip to seal the flash memory and perform a soft-reboot.
send_cmd("272BFDFFF86576D6") 
# Pushing an empty 32-byte payload to flush the write buffer.
send_data("FF000000000000000000000000000000") 

# We MUST wait for the hardware to fully restart and reconnect to the USB bus.
print(f"⏳ Waiting 1.5s for hardware soft-reboot...")
time.sleep(1.5) 

print("\n🛠️ 7. Applying Runtime System Parameters to Active RAM...")
# CRITICAL FIX 2: After the soft-reboot, the mouse goes into a "coma" idle state. 
# We MUST send these commands to physically wake up the laser tracking sensor.
hz_val = {1000:1, 500:2, 250:4, 125:8}[POLLING_RATE]
# Command 01H: Sets the Active Polling Rate to wake the USB interrupt pipe
send_cmd(build_cmd([0x01, hz_val, 0, 0, 0, 0, 0])) 
# Command 0EH: Sets Hardware Sensitivity to 100% (0x64)
send_cmd(build_cmd([0x0E, 0x64, 0x64, 0, 0, 0, 0])) 
# Command 04H: Sets Hardware Sensor Lift & Debounce Time
send_cmd(build_cmd([0x04, 0x01, KEY_RESPONSE_MS, 0, 0, 0, 0])) 

# Finish by applying software-level settings to the Windows OS.
apply_os_settings()

print(f"\n🎉 SUCCESS! Time: {time.perf_counter() - start_time:.2f}s")