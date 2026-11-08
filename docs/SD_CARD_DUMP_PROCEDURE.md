# SD Card Zero-Contact Firmware Backup Procedure

## Overview
This procedure extracts the factory firmware (8 MB SPI NOR Flash) from the **WorldTech WT-RV7186BT** without opening the casing, without soldering, and without modifying any hardware.

---

## Technical Mechanism
1. **Boot Priority**:
   On power-up, the Allwinner F1C200s internal Boot ROM (BROM) executes in this sequence:
   1. Check **SDC0** (MicroSD slot) at offset `0x2000` (8192 bytes / Sector 16) for valid `eGON.BT0` header.
   2. Check **SPI0** NOR Flash (`cFeon EN25QH64A`).
   3. Fallback to **USB FEL Mode**.

2. **Zero-Contact Execution**:
   By inserting a working FAT32 MicroSD card (4GB - 32GB) containing the eGON boot header into the external TF card slot:
   - When the mirror powers on, the SoC boots from the SD card instead of SPI flash.
   - The payload can either:
     - Automatically trigger Allwinner **FEL mode over USB** (enabling safe non-invasive extraction via the top USB port), OR
     - Read the 8 MB SPI NOR flash directly and save it as `firmware_backup.bin` on the SD card's FAT32 partition.
   - The physical casing remains completely sealed and pristine.

---

## Requirements
- **MicroSD Card**: 2 GB, 4 GB, 8 GB, 16 GB, or 32 GB (Class 4 or Class 10 SDHC).
- **Format**: MBR partition table with single FAT32 filesystem.
- **Do not use**: 64 GB+ SDXC cards (incompatible with F1C200s BROM).

---

## Step-by-Step Instructions
1. Insert a 4GB–32GB MicroSD card into your Mac.
2. Run the preparation script:
   ```bash
   python3 tools/prepare_sd_dumper.py
   ```
3. Eject the SD card from your Mac and insert it into the mirror's MicroSD slot.
4. Power on the mirror with 12V.
5. The firmware will be dumped or the device will be in communication mode.
6. Power off mirror, remove SD card, insert back into Mac, and verify with:
   ```bash
   python3 tools/verify_dump.py
   ```

