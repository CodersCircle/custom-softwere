#!/usr/bin/env python3
"""
Allwinner FEL Mode Device Detector via libusb (ctypes)
"""
import ctypes
import sys

AW_VID = 0x1F3A
AW_PID = 0xEFE8

def check_fel():
    libusb_paths = [
        "/opt/homebrew/opt/libusb/lib/libusb-1.0.dylib",
        "/opt/homebrew/lib/libusb-1.0.dylib",
        "/usr/local/lib/libusb-1.0.dylib",
        "libusb-1.0.dylib",
    ]
    lib = None
    for p in libusb_paths:
        try:
            lib = ctypes.CDLL(p)
            break
        except Exception:
            continue

    if not lib:
        print("[!] libusb not found.")
        return False

    ctx = ctypes.c_void_p()
    ret = lib.libusb_init(ctypes.byref(ctx))
    if ret < 0:
        print(f"[!] libusb_init failed: {ret}")
        return False

    lib.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p
    lib.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
    handle = lib.libusb_open_device_with_vid_pid(ctx, AW_VID, AW_PID)
    if handle:
        print("[+] SUCCESS: Allwinner FEL Device Detected! (0x1f3a:0xefe8)")
        lib.libusb_close(handle)
        lib.libusb_exit(ctx)
        return True
    else:
        print("[-] Allwinner FEL Device not found.")
        lib.libusb_exit(ctx)
        return False

if __name__ == "__main__":
    found = check_fel()
    sys.exit(0 if found else 1)

