#!/usr/bin/env python3
"""
Allwinner FEL Mode Device Detector & Monitor via libusb (ctypes)
WorldTech WT-RV7186BT (Allwinner F1C200s)
"""
import ctypes
import time
import sys

AW_VID = 0x1F3A
AW_PID = 0xEFE8

def get_libusb():
    libusb_paths = [
        "/opt/homebrew/opt/libusb/lib/libusb-1.0.dylib",
        "/opt/homebrew/lib/libusb-1.0.dylib",
        "/usr/local/lib/libusb-1.0.dylib",
        "libusb-1.0.dylib",
    ]
    for p in libusb_paths:
        try:
            return ctypes.CDLL(p)
        except Exception:
            continue
    return None

def check_fel_once(lib, ctx):
    lib.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p
    lib.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
    handle = lib.libusb_open_device_with_vid_pid(ctx, AW_VID, AW_PID)
    if handle:
        lib.libusb_close(handle)
        return True
    return False

def main():
    watch = "--watch" in sys.argv
    lib = get_libusb()
    if not lib:
        print("[!] Error: libusb-1.0.dylib not found on system.")
        sys.exit(1)

    ctx = ctypes.c_void_p()
    ret = lib.libusb_init(ctypes.byref(ctx))
    if ret < 0:
        print(f"[!] libusb_init failed with code: {ret}")
        sys.exit(1)

    if not watch:
        found = check_fel_once(lib, ctx)
        if found:
            print("[+] SUCCESS: Allwinner FEL Device Detected! (VID=0x1f3a, PID=0xefe8)")
        else:
            print("[-] Allwinner FEL Device not found.")
        lib.libusb_exit(ctx)
        sys.exit(0 if found else 1)

    print("[*] Monitoring for Allwinner FEL Device (VID=0x1f3a, PID=0xefe8)...")
    print("[*] (Press Ctrl+C to cancel at any time)")
    print("[*] Ready. Power ON the mirror while holding Pin 1 to GND for 1-2 seconds.")

    start = time.time()
    try:
        while time.time() - start < 120:  # 2 minute timeout
            if check_fel_once(lib, ctx):
                print("\n=======================================================")
                print("  🎉 SUCCESS! ALLWINNER FEL RECOVERY DEVICE CONNECTED! ")
                print("  VID: 0x1F3A  |  PID: 0xEFE8                          ")
                print("=======================================================\n")
                lib.libusb_exit(ctx)
                sys.exit(0)
            print(".", end="", flush=True)
            time.sleep(0.5)
        print("\n[-] Timeout (120s): No FEL device detected.")
    except KeyboardInterrupt:
        print("\n[*] Monitor stopped by user.")
    
    lib.libusb_exit(ctx)
    sys.exit(1)

if __name__ == "__main__":
    main()
