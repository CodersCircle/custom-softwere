#!/usr/bin/env python3
"""
Allwinner FEL Protocol Client for macOS (via libusb ctypes)
WorldTech WT-RV7186BT (Allwinner F1C200s)
100% local, no external packages required.
"""
import ctypes
import struct
import sys
import time

AW_VID = 0x1F3A
AW_PID = 0xEFE8

# Allwinner USB Command / Status Magic
AWUC_MAGIC = 0x43555741  # "AWUC" in LE
AWUS_MAGIC = 0x53555741  # "AWUS" in LE

# FEL Commands
FEL_CMD_VERIFY = 0x0001
FEL_CMD_SWITCH = 0x0002
FEL_CMD_WRITE  = 0x0101
FEL_CMD_EXEC   = 0x0102
FEL_CMD_READ   = 0x0103

def get_libusb():
    paths = [
        "/opt/homebrew/opt/libusb/lib/libusb-1.0.dylib",
        "/opt/homebrew/lib/libusb-1.0.dylib",
        "/usr/local/lib/libusb-1.0.dylib",
        "libusb-1.0.dylib",
    ]
    for p in paths:
        try:
            return ctypes.CDLL(p)
        except Exception:
            continue
    return None

class FELClient:
    def __init__(self):
        self.lib = get_libusb()
        if not self.lib:
            raise RuntimeError("libusb-1.0.dylib not found")
        self.ctx = ctypes.c_void_p()
        self.handle = None
        self.ep_out = 0x01
        self.ep_in  = 0x82

    def connect(self):
        ret = self.lib.libusb_init(ctypes.byref(self.ctx))
        if ret < 0:
            return False

        self.lib.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p
        self.lib.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
        self.handle = self.lib.libusb_open_device_with_vid_pid(self.ctx, AW_VID, AW_PID)
        if not self.handle:
            return False

        # Claim interface 0
        self.lib.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
        ret = self.lib.libusb_claim_interface(self.handle, 0)
        return True

    def close(self):
        if self.handle:
            self.lib.libusb_release_interface(self.handle, 0)
            self.lib.libusb_close(self.handle)
            self.handle = None
        if self.ctx:
            self.lib.libusb_exit(self.ctx)
            self.ctx = None

    def bulk_write(self, data, timeout=2000):
        transferred = ctypes.c_int(0)
        c_buf = (ctypes.c_char * len(data)).from_buffer_copy(data)
        ret = self.lib.libusb_bulk_transfer(
            self.handle, self.ep_out, c_buf, len(data),
            ctypes.byref(transferred), timeout
        )
        return ret == 0, transferred.value

    def bulk_read(self, length, timeout=2000):
        transferred = ctypes.c_int(0)
        c_buf = (ctypes.c_char * length)()
        ret = self.lib.libusb_bulk_transfer(
            self.handle, self.ep_in, c_buf, length,
            ctypes.byref(transferred), timeout
        )
        return ret == 0, bytes(c_buf[:transferred.value])

    def send_awuc(self, cmd, length):
        # AWUC: magic(4), tag(4), data_len(4), reserved(4), cmd(4), pad(12) = 32 bytes
        tag = 0x12345678
        awuc = struct.pack("<IIIIII8s", AWUC_MAGIC, tag, length, 0, 0x12, cmd, b"\x00"*8)
        ok, _ = self.bulk_write(awuc)
        return ok

    def read_awus(self):
        ok, data = self.bulk_read(13)
        if ok and len(data) >= 13:
            magic, tag, residue, status = struct.unpack("<IIIB", data[:13])
            return magic == AWUS_MAGIC and status == 0
        return False

    def verify_device(self):
        # Request 32 bytes device info
        if not self.send_awuc(FEL_CMD_VERIFY, 32):
            return None
        ok, resp = self.bulk_read(32)
        if not ok or len(resp) < 32:
            return None
        self.read_awus()
        # Parse FEL verify response
        board_id, flen, fel_mode = struct.unpack("<III", resp[:12])
        return {
            "board_id": f"0x{board_id:08x}",
            "raw": resp.hex()
        }

def main():
    client = FELClient()
    print("[*] Connecting to Allwinner FEL device...")
    if not client.connect():
        print("[-] FEL device not found. Make sure device is powered in FEL mode.")
        sys.exit(1)

    print("[+] Connected to Allwinner FEL device!")
    info = client.verify_device()
    if info:
        print(f"[+] SoC Verified: Board ID = {info['board_id']}")
    else:
        print("[!] Could not read board ID, but USB connection is alive.")

    client.close()

if __name__ == "__main__":
    main()
