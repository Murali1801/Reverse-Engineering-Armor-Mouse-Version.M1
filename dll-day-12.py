import ctypes
import time

# =====================================================================
# 1. USER CONFIGURATION (CUSTOMIZE EVERYTHING HERE)
# =====================================================================

# --- POLLING RATE (Report Rate) ---
# Command 01H: Set USB refresh frequency
# 1000Hz (FD) = 1ms, 500Hz (FC) = 2ms, 250Hz (FA) = 4ms, 125Hz (F6) = 8ms
POLLING_RATE_CMD = "01010000000000FD" # 1000Hz selected

# --- SYSTEM SETTINGS (From Software Menus) ---
# Mouse Move Speed: Command 0EH. Range 1-200 (64 Hex = 100% Speed)
MOVE_SPEED = 100 

# Key Response (Debounce): Command 04H. Prevents accidental double-clicks.
# Range 4 to 100ms. 0C Hex = 12ms
KEY_RESPONSE_MS = 12 

# Double Click Speed: Software timing for multi-click registration.
# Command 0AH (Fire Button) default speed is often 32 Hex (50ms).
DOUBLE_CLICK_SPEED = 50 

# --- DPI SPEEDS (Stages 1-6) ---
# Sensor resolution in steps of 100.
DPI_STAGES = [
    400,   # Stage 1: (04 Hex)
    800,   # Stage 2: (08 Hex)
    1200,  # Stage 3: (0C Hex)
    2400,  # Stage 4: (18 Hex)
    3200,  # Stage 5: (20 Hex)
    6200   # Stage 6: (3E Hex)
]

# --- DPI COLORS (RGB) ---
# Hexadecimal color codes (RRGGBB).
DPI_COLORS = [
    "FF0055",  # Neon Pink
    "00FF00",  # Pure Green
    "0000FF",  # Pure Blue
    "FFFF00",  # Bright Yellow
    "FF8800",  # Vivid Orange
    "00FFFF"   # Cyan/Aqua
]

# --- BUTTON SET 1 (Physical Buttons 1-8) ---
# Format: [Command][Modifier][Key/Action][Number/State]
BUTTONS_BLOCK_1 = [
    "0100F000",  # Slot 1: Left Click (01=Standard, F0=Left)
    "0100F100",  # Slot 2: Right Click (F1=Right)
    "0100F200",  # Slot 3: Middle Click (F2=Middle)
    "0100F400",  # Slot 4: Forward (F4=Button 5)
    "0100F300",  # Slot 5: Backward (F3=Button 4)
    "07000300",  # Slot 6: DPI Cycle (07=DPI Cmd, 03=Cycle Loop)
    "00000000",  # Slot 7: Unassigned (00=Button Off)
    "00000000"   # Slot 8: Unassigned
]

# --- BUTTON SET 2 (Scroll & Advanced 9-16) ---
BUTTONS_BLOCK_2 = [
    "00000000",  # Slot 9: Unassigned
    "00000000",  # Slot 10: Unassigned
    "00000000",  # Slot 11: Unassigned
    "00000000",  # Slot 12: Unassigned
    "00000000",  # Slot 13: Unassigned
    "00000000",  # Slot 14: Unassigned
    "04000100",  # Slot 15: Scroll Up (04=Scroll, 01=Up)
    "04000200"   # Slot 16: Scroll Down (02=Down)
]

# =====================================================================
# 2. DRIVER ENGINE (COMMUNICATION LOGIC)
# =====================================================================
try:
    # Load the vendor DLL provided for USB communication
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}"); exit()

# Set Hardware Identity: Holtek VID (04D9), Gaming Mouse PID (A09F)
driver.Set_VIDPID(0x04D9, 0xA09F)

def send_cmd(hex_str):
    """Sends 8-byte Feature Reports (Command Headers)"""
    data = bytes.fromhex(hex_str)
    driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    time.sleep(0.02)

def send_data(hex_str):
    """Sends 32-byte Output Reports (Data Payloads)"""
    data = bytes.fromhex(hex_str)
    # Pad with zeros to reach the required 32-byte hardware buffer
    if len(data) < 32: data += b'\x00' * (32 - len(data))
    driver.WriteUSB((ctypes.c_byte * 32)(*data), 32)
    time.sleep(0.02)

# =====================================================================
# 3. DYNAMIC PAYLOAD BUILDER (AUTOMATED MATH)
# =====================================================================
# Generate Move Speed Command (0EH) with calculated Checksum
val_hex = f"{MOVE_SPEED:02X}"
move_speed_cmd = f"0E{val_hex}{val_hex}0000000000"
cs_0e = (255 - (0x0E + MOVE_SPEED + MOVE_SPEED)) & 0xFF
move_speed_cmd += f"{cs_0e:02X}"

# Generate Key Response Command (04H) with LOD 1 and calculated Checksum
key_resp_cmd = f"0401{KEY_RESPONSE_MS:02X}0000000000"
cs_04 = (255 - (0x04 + 0x01 + KEY_RESPONSE_MS)) & 0xFF
key_resp_cmd += f"{cs_04:02X}"

# Concatenate RGB Colors (18 bytes total)
color_payload = "".join(DPI_COLORS)

# Convert DPI values to hex steps and add 7C78 Calibration Suffix
dpi_payload = "".join([f"{int(dpi/100):02X}" for dpi in DPI_STAGES]) + "7C78"

# =====================================================================
# 4. HARDWARE FLASHING SEQUENCE
# =====================================================================
print("🔌 Opening USB Handles...")
driver.Open_FeatureDevice(); driver.Open_ReportDevice()

print("\n🔓 1. Initializing Hardware Waking (Vendor Handshake)...")
send_cmd("08AACCEE0000001E") # Wake up code
send_cmd("252BA5FFF0E0E6EE") # Security bypass

print("\n🛠️ 2. Applying System Parameters (Polling, Speed, Debounce)...")
send_cmd(POLLING_RATE_CMD) # Set Hz
send_cmd(move_speed_cmd)   # Set Sensitivity
send_cmd(key_resp_cmd)     # Set Debounce

print("\n🎨 3. Flashing DPI Profiles & LED Colors...")
send_cmd("272A85FFF0657636") # Address for Colors
send_data(color_payload)
send_cmd("272BFDFFE06D76B6") # Address for DPI steps
send_data(dpi_payload)

print("\n⚙️ 4. Flashing Button Mappings...")
send_cmd("272D5DFFE8557876") # Address for Buttons 1-8
send_data("".join(BUTTONS_BLOCK_1))
send_cmd("272D25FF00557876") # Address for Buttons 9-16
send_data("".join(BUTTONS_BLOCK_2))

print("\n🏁 5. Locking Configuration & Committing to Flash...")
send_cmd("272BFDFFF86576D6") # Save command
send_data("FF000000000000000000000000000000")
send_cmd("08AACCEE0000001E") # Close session

print("\n🎉 SUCCESS! Your mouse is now running your custom firmware.")