import ctypes
import time

# --- Load the Mouse Driver DLL ---
try:
    driver = ctypes.CDLL("./MSDriver.dll")
except Exception as e:
    print(f"❌ DLL Error: {e}")
    exit()

VID, PID = 0x04D9, 0xA09F
driver.Set_VIDPID(VID, PID)

def send_packet(hex_str, is_command=True):
    """Sends exactly 8 bytes to the mouse"""
    data = bytes.fromhex(hex_str)
    buffer = (ctypes.c_byte * 8)(*data)
    result = driver.SetFeature(buffer, 8)
    
    pkt_type = "Command" if is_command else "Payload"
    if result == 0:
        print(f"❌ FAILED to send {pkt_type}: {hex_str}")
    else:
        print(f"✅ Sent {pkt_type}: {hex_str}")
    time.sleep(0.02) 

print("🔌 Connecting to Mouse...")
# WE MUST OPEN BOTH PIPELINES!
feature_status = driver.Open_FeatureDevice()
report_status = driver.Open_ReportDevice()
print(f"Device Status -> Feature: {feature_status}, Report: {report_status}")

print("\n🔓 Unlocking Hardware...")
send_packet("252BA5FFF0E0E6EE") 

print("\n⚡ Sending DPI Header...")
send_packet("272BFDFFE06D76B6")

# Stage 1: 400, Stage 2: 800, Stage 3: 1200
# Stage 4: 2400, Stage 5: 3200, Stage 6: 6200
hex_payload = "04080C18203E7C78"
print(f"\n💾 Writing Custom DPI Data: {hex_payload}")
send_packet(hex_payload, is_command=False)

print("\n🔒 Saving to Mouse Memory...")
send_packet("08AACCEE0000001E")

print("\n🎉 DONE! Press the DPI cycle button on your mouse to test it.")