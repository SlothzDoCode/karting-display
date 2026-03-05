#! imports
from bleak import BleakScanner

Basline_rssi = None
basline_set = False

def detection_callback(device, display_data):
    global basline_set, Basline_rssi
    
    rssi = device.rssi
    start_pressed = display_data[0]
    
    if start_pressed and not basline_set:
        Basline_rssi = rssi
        basline_set = True
        print("📍 Start line set")
        return