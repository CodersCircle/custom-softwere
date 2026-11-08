# Firmware Backup & Safe Acquisition Plan

## Objective
Safely create bit-perfect, read-only backups of the factory firmware stored in the onboard 8 MB SPI NOR Flash (`cFeon EN25QH64A`) without altering or damaging the device.

---

## 1. Safety Rules & Pre-Flight Checklist

> [!CAUTION]
> **Strict Operational Constraints:**
> - **Zero Write Operations**: Never execute write, erase, or program commands against the flash chip during backup.
> - **Voltage Clamping**: All logic lines must strictly stay at **3.3 V**. Standard CH341A programmers often output 5V on data lines unless modified or 3.3V jumpered. Always meter programmer pins with a digital multimeter before clipping to the board!
> - **Complete Power Isolation**: During in-circuit clip programming, the mirror device must be completely disconnected from its 12V/ACC automotive harness and external power supplies.
> - **Do Not Trust USB-A**: Do not plug the device's USB-A port into your Mac with a male-to-male USB-A cable until the VBUS and data pins have been electrically probed.

---

## 2. Acquisition Strategies

### Method A: Hardware SPI Read via SOIC-8 Clip (Gold Standard)

This method directly interfaces with the `cFeon EN25QH64A` 8-pin chip using an external hardware programmer while the rest of the board is unpowered.

#### Equipment Required:
1. **SOIC-8 / SOP-8 Test Clip** (e.g., Pomona 5250 or equivalent clip with clean gold contacts).
2. **3.3V SPI Programmer**:
   - CH341A Programmer (must verify 3.3V logic fix on pin 28 / data pins) OR
   - FT232H / FT2232H USB-to-SPI board OR
   - Raspberry Pi / RP2040 (Raspberry Pi Pico running `picoprobe` or `pico-serprog`)
3. **Digital Multimeter (DMM)** for continuity and voltage verification.

#### Step-by-Step Procedure:
1. Disconnect all external power and cables from the mirror device.
2. Verify pin 1 location on the `EN25QH64A` (marked by dot on the chip body).
3. Connect programmer to macOS host (do not connect clip to board yet).
4. Verify with DMM that VCC and data lines output 3.3 V (not 5.0 V).
5. Attach SOIC-8 clip securely over the `EN25QH64A` chip pins.
6. Run detection command:
   ```bash
   flashrom -p <programmer_type>
   ```
   *Expected output*: `Found Eon flash chip "EN25QH64" (8192 kB, SPI)`
7. Perform first read:
   ```bash
   flashrom -p <programmer_type> -r firmware_dump_1.bin
   ```
8. Perform second independent read:
   ```bash
   flashrom -p <programmer_type> -r firmware_dump_2.bin
   ```
9. Verify integrity:
   ```bash
   sha256sum firmware_dump_1.bin firmware_dump_2.bin
   ```
   Both SHA-256 hashes **must be identical**. If hashes differ, reseat the clip and check for ground noise or high SPI clock speeds.

---

### Method B: Non-Invasive SD Card Extraction (Zero-Soldering)

The Allwinner F1C200s internal Boot ROM (BROM) executes the following boot priority on power-on:
1. **SDC0 (MicroSD slot)** — Checks for an `eGON.BT0` header.
2. **SPI0 NOR Flash** (`EN25QH64A`).
3. **USB FEL Mode** (fallback if neither is valid).

Because SDC0 has higher priority than SPI NOR flash, a custom non-invasive payload (e.g. minimal U-Boot or a bare-metal ARM dumper written to an SD card) can be booted from the MicroSD slot to dump the SPI NOR flash directly to a file on the SD card (`/dump.bin`).

#### Advantages:
- 100% non-invasive (no clip, no opening casing once verified).
- Eliminates any risk of electrostatic discharge (ESD) or bus contention on SPI lines.
- Leaves SPI flash completely untouched in hardware.

---

### Method C: Allwinner USB FEL Mode

Allwinner SoCs feature a built-in ROM routine called **FEL mode** accessible over USB OTG.
- With `sunxi-tools` (`sunxi-fel`), the host computer can read/write memory and dump SPI flash directly:
  ```bash
  sunxi-fel spiflash-read 0 0x800000 firmware_fel_dump.bin
  ```

#### Safety Prerequisite:
- Trace the USB-A port's D+ and D- lines to confirm whether they connect directly to the F1C200s USB pins.
- Check if VBUS has back-feed voltage from the internal buck regulator.
- If verified safe, trigger FEL mode either via a special MicroSD card ("fel-boot.img") or by holding the SPI flash chip select pin during boot.

---

## 3. Post-Acquisition Verification & Analysis

Once a verified dump is acquired:
1. **Calculate Hashes**:
   ```bash
   shasum -a 256 firmware_dump.bin > firmware_dump.bin.sha256
   ```
2. **Make File Read-Only**:
   ```bash
   chmod 444 firmware_dump.bin
   ```
3. **Entropy & Header Inspection**:
   ```bash
   binwalk firmware_dump.bin
   hexdump -C -n 512 firmware_dump.bin
   strings -n 8 firmware_dump.bin | head -n 50
   ```
4. **Identify Partitions**:
   - Allwinner eGON bootloader signature (`eGON.BT0` / `eGON.DIR`).
   - Melis OS or Linux kernel image (uImage / zImage).
   - Filesystem types: SquashFS, CramFS, JFFS2, or raw binary asset tables (fonts, UI bitmaps, boot logos).
