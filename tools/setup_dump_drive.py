import os
import sys

mount_point = "/Volumes/DUMPER"
if not os.path.exists(mount_point):
    print("[-] Error: /Volumes/DUMPER not mounted.")
    sys.exit(1)

# Autorun script for Linux/Melis OS that attempts to dump MTD flash to USB
script_content = """#!/bin/sh
echo "=== Allwinner Firmware Dumper Script ==="
# Try dumping all MTD partitions
for dev in /dev/mtdblock* /dev/mtd*; do
    if [ -e "$dev" ]; then
        echo "Dumping $dev..."
        dd if="$dev" of="./dump_$(basename $dev).bin" bs=64k
    fi
done

# Try dumping raw SPI flash
if [ -e "/dev/spidev0.0" ]; then
    dd if=/dev/spidev0.0 of=./dump_spi.bin bs=64k count=128
fi

echo "Done."
sync
"""

files = ["auto_run.sh", "autorun.sh", "test.sh", "factory.sh"]
for f in files:
    path = os.path.join(mount_point, f)
    with open(path, "w") as fp:
        fp.write(script_content)
    os.chmod(path, 0o755)

print(f"[+] Successfully prepared auto-dump scripts on {mount_point}!")
