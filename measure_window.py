import win32gui

def get_window_rect(classname):
    hwnd = win32gui.FindWindow(None, classname)
    if not hwnd:
        print("Window not found")
        return None
    rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    
    c_width = client_rect[2] - client_rect[0]
    c_height = client_rect[3] - client_rect[1]
    
    print(f"Window: {width}x{height}")
    print(f"Client: {c_width}x{c_height}")
    return width, height

get_window_rect("Armor Version.M1")
