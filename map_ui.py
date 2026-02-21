# map_ui.py
import os
import xml.etree.ElementTree as ET

# Define the path to the resources
RES_FOLDER = "res"

def parse_xml_for_buttons(filename):
    path = os.path.join(RES_FOLDER, filename)
    if not os.path.exists(path):
        return

    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        print(f"\n📂 SCANNING: {filename}")
        print("-" * 40)
        
        # DuiLib usually uses <Button> or <Option> (for radio buttons)
        for btn in root.iter('Button'):
            name = btn.get('name')
            text = btn.get('text')
            cmd = btn.get('cmd') # Sometimes used for commands
            
            if name or text:
                print(f"  🔘 BUTTON FOUND:")
                print(f"     Name (ID): {name}")
                print(f"     Label:     {text}")
                
        for opt in root.iter('Option'):
            name = opt.get('name')
            group = opt.get('group')
            print(f"  🔘 TAB/OPTION FOUND:")
            print(f"     Name (ID): {name}")
            print(f"     Group:     {group}")

    except Exception as e:
        print(f"Error parsing {filename}: {e}")

# Scan the most important files based on your file list
files_to_scan = [
    "main.xml",           # Likely holds the Close/Minimize/Menu buttons
    "buttonpage.xml",     # Likely holds key mapping
    "performancepage.xml",# Likely holds DPI settings
    "lightpage.xml",      # Likely holds RGB settings
    "macrodirmenu.xml"    # Likely holds macro controls
]

print("🔍 STARTING UI MINING...")
for f in files_to_scan:
    parse_xml_for_buttons(f)

print("\n" + "="*40)
print("👉 INSTRUCTIONS:")
print("1. Look for the 'Name (ID)' of the buttons you want (e.g., 'btn_apply').")
print("2. Copy those names into your 'armor_control.py' script.")
print("="*40)