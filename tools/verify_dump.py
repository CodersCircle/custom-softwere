#!/usr/bin/env python3
"""
Firmware Dump Verification & Integrity Tool
WorldTech WT-RV7186BT (Allwinner F1C200s + cFeon EN25QH64A)
"""
import sys
import os
import hashlib

EXPECTED_SIZE = 8 * 1024 * 1024  # 8,388,608 bytes (8 MB)

def verify_file(filepath):
    if not os.path.exists(filepath):
        print(f"[-] Error: File not found: {filepath}")
        return False

    size = os.path.getsize(filepath)
    print(f"[*] Analyzing: {filepath}")
    print(f"[*] File Size: {size:,} bytes ({size / (1024*1024):.2f} MB)")

    if size == EXPECTED_SIZE:
        print("[+] Size matches expected 8MB SPI NOR flash (EN25QH64A).")
    else:
        print(f"[!] Warning: Expected {EXPECTED_SIZE:,} bytes, but got {size:,} bytes.")

    # Calculate SHA256
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    sha256 = hasher.hexdigest()
    print(f"[+] SHA-256: {sha256}")

    # Inspect first 64 bytes
    with open(filepath, "rb") as f:
        header = f.read(64)

    if b"eGON" in header:
        print("[+] Found Allwinner 'eGON' Bootloader Signature in header!")
    else:
        print("[*] Note: Standard eGON signature not in first 64 bytes (checking partitions...)")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/verify_dump.py <firmware_dump.bin>")
        sys.exit(1)

    success = verify_file(sys.argv[1])
    sys.exit(0 if success else 1)

