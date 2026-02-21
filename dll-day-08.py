import ctypes
import time

try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

VID, PID = 0x04D9, 0xA09F
driver.Set_VIDPID(VID, PID)

def send_cmd(hex_str):
    data = bytes.fromhex(hex_str)
    res = driver.SetFeature((ctypes.c_byte * 8)(*data), 8)
    print(f"  [Command] {hex_str} | Res: {res}")
    time.sleep(0.02)

def send_data(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 32:
        data += b'\x00' * (32 - len(data))
    
    buffer = (ctypes.c_byte * 32)(*data)
    res = driver.WriteUSB(buffer, 32)
    print(f"  [Payload] {hex_str[:16]}... | Res: {res}")
    time.sleep(0.02)

# ==========================================
# EXACT 32-BYTE PAYLOADS
# ==========================================
# 6 Colors (Pink, Green, Blue, Yellow, Orange, Cyan) + 2 White Padding Slots
COLOR_BLOCK = "FF00550000FF00000000FF00FFFF0000FF88000000FFFF00FFFFFF00FFFFFF00"

# 6 DPI Stages (04080C18203E) 
# The last two bytes (FC F8) have Bit 7 set to '1' to officially Disable stages 7 and 8!
DPI_BLOCK = "04080C18203EFCF8"

# EXACT BUTTON MATRIX FROM THE HOLTEK DATASHEET:
# L-Click(0100F000), R-Click(0100F100), M-Click(0100F200), Forward(0100F400), Back(0100F300)
# And the holy grail: DPI+ Loop = 07000300
BTN_BLOCK_1 = "0100F0000100F1000100F2000100F4000100F300070003000000000000000000"

# Scroll Wheel Matrix (Fixed to slots 15/16 per documentation)
# Scroll Up = 04000100, Scroll Down = 04000200
BTN_BLOCK_2 = "0000000000000000000000000000000000000000000000000400010004000200"

print("🔌 Connecting to Mouse Pipelines...")
driver.Open_FeatureDevice()
driver.Open_ReportDevice()

print("\n🔓 1. Handshake...")
send_cmd("08AACCEE0000001E")
time.sleep(0.05)
send_cmd("252BA5FFF0E0E6EE")

print("\n🛠️ 2. Hardware Initialization...")
send_cmd("272BDDFFE8D57676")
send_cmd("272BD5FFE8ED7676")
send_cmd("272B7DFFD01D7676")
send_cmd("272B9D0498457676")
send_cmd("272B5DFFD0524E8E")

print("\n🎨 3. Injecting Colors...")
send_cmd("272A85FFF0657636")
send_data(COLOR_BLOCK) 
send_cmd("272A8DFFE8657636")
send_data(COLOR_BLOCK) 

print("\n⚡ 4. Injecting Custom DPI Block (With Disables!)...")
send_cmd("272BFDFFE06D76B6")
send_data(DPI_BLOCK)

print("\n⚙️ 5. Restoring TRUE Factory Buttons (07000300 Loop!)...")
send_cmd("272D5DFFE8557876")
send_data(BTN_BLOCK_1) 
send_cmd("272D25FF00557876")
send_data(BTN_BLOCK_2) 

print("\n🏁 6. Finalization...")
send_cmd("272BFDFFF86576D6")
send_data("FF000000000000000000000000000000")

print("\n🔒 7. Saving to Memory...")
send_cmd("08AACCEE0000001E")

print("\n🎉 COMPLETE! Press the DPI button!")