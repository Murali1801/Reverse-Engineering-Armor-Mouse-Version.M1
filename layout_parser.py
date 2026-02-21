import xml.etree.ElementTree as ET
import os
import json

class LayoutParser:
    def __init__(self, res_dir):
        self.res_dir = res_dir
        self.button_map = {}
        # Default window content area offset (caption="0,0,0,76" implies 76px top caption)
        self.window_caption_height = 76 
        
    def parse_padding(self, padding_str):
        if not padding_str: return (0, 0, 0, 0)
        try:
            parts = [int(p) for p in padding_str.split(',')]
            if len(parts) == 4: return tuple(parts)
            return (0,0,0,0)
        except: return (0,0,0,0)

    def parse_size(self, elem, parent_w, parent_h):
        # Parses width/height attributes
        w = elem.get('width')
        h = elem.get('height')
        
        # Simple integer parsing, ignoring % for now as they seem rare in this specific XML set
        width = int(w) if w and w.isdigit() else 0
        height = int(h) if h and h.isdigit() else 0
        
        return width, height

    def process_element(self, element, x, y, parent_w, parent_h):
        tag = element.tag
        name = element.get('name')
        print(f"DEBUG: Processing <{tag}> name='{name}' at ({x}, {y})")
        
        # Parse attributes
        padding = self.parse_padding(element.get('padding'))
        # Adjust current position by padding-left and padding-top
        current_x = x + padding[0]
        current_y = y + padding[1]
        
        # Determine element size
        width, height = self.parse_size(element, parent_w, parent_h)
        
        # If it's a target button, record it
        if name and ('btn' in name or 'option' in name or 'combo' in name or 'Button' in tag or 'Option' in tag):
            # Center of the element
            center_x = current_x + (width // 2)
            center_y = current_y + (height // 2)
            self.button_map[name if name else tag] = (center_x, center_y)
            print(f"!!! FOUND BUTTON: {name if name else tag} at ({center_x}, {center_y}) !!!")

        # Container Logic
        # Calculate available size for children (not strictly implemented for auto-sizing, assuming fixed sizes for now)
        
        # Handle INCLUDES
        if tag == 'Include':
            source = element.get('source')
            if source:
                self.parse_file(source, current_x, current_y, parent_w, parent_h)
            # Include itself doesn't have size usually, but children do. 
            # For this parser, we assume Include is just an insertion point.
            
        # Handle LAYOUTS
        if 'HorizontalLayout' in tag:
            child_x = current_x
            child_y = current_y
            max_h = 0
            
            for child in element:
                if child.tag == 'Control' and not child.get('width') and not child.get('height'):
                     # Spacer 'Control' might take remaining space, simply ignored for static coords
                     pass
                
                # Recursively process child
                cw, ch = self.process_element(child, child_x, child_y, width, height)
                
                # Advance X
                child_x += cw
                max_h = max(max_h, ch)
                
            # Horizontal layout takes width of all children (roughly) or specific width
            return (width if width else child_x - current_x), (height if height else max_h)

        elif 'VerticalLayout' in tag or tag == 'Window': # Treat Window as vertical root
            child_x = current_x
            child_y = current_y
            max_w = 0
            
            for child in element:
                cw, ch = self.process_element(child, child_x, child_y, width, height)
                
                # Advance Y
                child_y += ch
                max_w = max(max_w, cw)
                
            return (width if width else max_w), (height if height else child_y - current_y)
            
        elif 'TabLayout' in tag:
            # All children start at same x, y
            max_w, max_h = 0, 0
            for child in element:
                 cw, ch = self.process_element(child, current_x, current_y, width, height)
                 max_w = max(max_w, cw)
                 max_h = max(max_h, ch)
            return (width if width else max_w), (height if height else max_h)

        else:
            # Leaf element (Button, Label, Control, etc.)
            return width + padding[0] + padding[2], height + padding[1] + padding[3]

    def parse_file(self, filename, x, y, w, h):
        path = os.path.join(self.res_dir, filename)
        print(f"--- Attempting to parse: {path} ---")
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            return
            
        file_size = os.path.getsize(path)
        print(f"File Size: {file_size} bytes")
        
        try:
            # Read logic with robust encoding handling
            with open(path, 'rb') as f:
                raw_bytes = f.read()
                print(f"Read {len(raw_bytes)} bytes from {filename}")
            
            # ET.fromstring can handle bytes and will respect the internal encoding declaration
            root = ET.fromstring(raw_bytes)
            print(f"XML structure parsed successfully for {filename}")
            self.process_element(root, x, y, w, h)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"EXCEPTION during {filename} parsing: {e}")
            import traceback
            traceback.print_exc()
            print(f"EXCEPTION during {filename} parsing: {e}")

    def run(self):
        try:
            print(f"Current CWD: {os.getcwd()}")
            if os.path.exists(self.res_dir):
                print(f"Res dir '{self.res_dir}' exists.")
            else:
                print(f"Res dir '{self.res_dir}' NOT FOUND!")

            # Start with main.xml
            print("Starting main.xml parse...")
            self.parse_file("main.xml", 0, 0, 1280, 750)
            
            # Save map
            with open("button_map.json", "w") as f:
                json.dump(self.button_map, f, indent=4)
            print(f"Extracted {len(self.button_map)} components to button_map.json")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRITICAL ERROR in run(): {e}")

if __name__ == "__main__":
    parser = LayoutParser("res")
    parser.run()
