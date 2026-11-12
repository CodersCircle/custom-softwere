"""Write the read-only dumper (u-boot-sunxi-with-spl.bin) to the SD card at 8 KiB offset.

Only touches the gap between the MBR and the FAT32 partition (8 KiB .. 1 MiB).
Refuses to run unless Disk 2 is the 8 GB USB SD card with partition 1 at 1 MiB.
"""
import hashlib, subprocess, sys, json

BIN = r"D:\IOT_PROJECTS\custom-softwere\sd-dumper\out\u-boot-sunxi-with-spl.bin"
DEV = r"\\.\PhysicalDrive2"
OFFSET = 8192
LIMIT = 1048576

info = json.loads(subprocess.check_output([
    "powershell", "-NoProfile", "-Command",
    "$d=Get-Disk -Number 2; $p=Get-Partition -DiskNumber 2 -PartitionNumber 1; "
    "@{bus=\"$($d.BusType)\";size=$d.Size;off=$p.Offset} | ConvertTo-Json"]))
if info["bus"] != "USB" or info["size"] != 8063549440 or info["off"] != LIMIT:
    sys.exit(f"ABORT: disk 2 does not look like the prepared SD card: {info}")

data = open(BIN, "rb").read()
expected = open(BIN + ".sha256").read().split()[0]
if hashlib.sha256(data).hexdigest() != expected:
    sys.exit("ABORT: binary SHA-256 mismatch")
if data[4:12] != b"eGON.BT0":
    sys.exit("ABORT: no eGON.BT0 header")
if OFFSET + len(data) > LIMIT:
    sys.exit("ABORT: binary would overlap FAT partition")

padded = data + b"\0" * (-len(data) % 512)
with open(DEV, "r+b", buffering=0) as f:
    f.seek(OFFSET)
    f.write(padded)
with open(DEV, "rb", buffering=0) as f:
    f.seek(OFFSET)
    back = f.read(len(padded))
print("readback", "OK" if back == padded else "MISMATCH", "bytes", len(data))
sys.exit(0 if back == padded else 1)

