# SD-Card-Only Firmware Backup — Feasibility Investigation

**Device:** WorldTech WT-RV7186BT (car mirror monitor, Bluetooth, touch)
**PCB:** WT-RV7186-TOUCH_V1.1
**Status:** Research / feasibility only. **No backup has been performed. Nothing has been run on the device.**

---

## 1. Summary (TL;DR)

| Question | Answer |
|---|---|
| Is SD-card-only backup possible? | **Possibly, at the SoC level — not yet confirmed for this board.** |
| Does the existing firmware support it? | **No evidence that it does.** No known export/dump/diagnostic feature. |
| Required mechanism | Use the F1C200s **Boot ROM (BROM)** SD-boot path to run a purpose-built, read-only dumper (for example, a custom mainline U-Boot build) from a **spare** SD card. The dumper reads the SPI flash into RAM and writes it to a FAT file on the same card. |
| Can the full internal flash be read? | **In theory, yes.** The boot flash is identified as a **cFeon EN25QH64A, 8 MiB SPI NOR** (see [HARDWARE.md](HARDWARE.md) and `images/crop_flash.png`). SPI NOR is fully readable by the SoC. This depends on the TF slot being wired to SDC0 (PF0–PF5), which is **not yet confirmed by measurement**. |
| Safest next step | Image the original SD card on the Mac, then check continuity from the TF slot to SDC0 with the board unpowered. Do not boot anything yet. |

---

## 2. Device evidence (from user photos)

| Item | Observed | Confidence |
|---|---|---|
| SoC | Silkscreen reads **"F1C200s"** (Allwinner, QFN-88) | High (visual) |
| Firmware string | Settings dialog: `soft version: V9.12BT-TP`, `Info: WT_RV7186BT_HD`, `date: 2021.12.13` | High (visual) |
| Version suffix | Screen shows **`-TP`**, not `-TF` as in the task brief | High. Note the difference. |
| PCB | `WT-RV7186-TOUCH_V1.1` | High |
| Crystal | 24.000 MHz (standard for F1C100s/F1C200s) | High |
| External ports | 3.5 mm jacks, **USB-A (host)**, **microSD/TF slot**, a button, and a pin-hole | High |
| Boot flash | SOP-8 next to the 24 MHz crystal, marked **`cFeon QH64A-104HIP`**, i.e. Eon **EN25QH64A**, 64 Mbit = **8,388,608 bytes** SPI NOR (repo `images/crop_flash.png`) | High (visual; JEDEC ID not yet read) |
| Other SOP-8 | `8002D / XS2180B` audio amplifier (per [HARDWARE.md](HARDWARE.md)), not storage | Medium |
| Bluetooth module | Separate BT antenna/module (`BT-ANT`) | Medium |
| UART test pads | Not identified in photos | Unknown |
| Settings menu | Shows "Factory default". **Must not be used.** | High |

---

## 3. Research findings

### 3.1 Allwinner F1C200s Boot ROM (BROM)
- The F1C200s is the `suniv` family: ARM926EJ-S CPU with **64 MB DDR in the same package**. It is the same die family as the F1C100s, which has 32 MB.
- Documented BROM boot order (linux-sunxi community, Lichee Pi Nano docs, mainline U-Boot `suniv` support):
  1. **SD card on SDC0** (pins PF0–PF5). The BROM looks for an `eGON.BT0` header at **8 KiB offset** (sector 16).
  2. **SPI NOR, then SPI NAND, on SPI0** (pins PC0–PC3).
  3. **USB FEL** (fallback) on the single USB OTG port.
- **What this means:** the SoC checks the SD card *before* internal flash. A card with a valid eGON image boots instead of the factory firmware. **Nothing in internal flash changes.** Remove the card and the factory boot path comes back.
- **Not verified for this board:** the TF slot may be wired to SDC0, or the vendor may have used other pins. If it is not on SDC0, BROM SD boot is impossible on this board.
- There is no secure-boot or eFuse lockout on the F1C100s/F1C200s, so BROM SD boot cannot be disabled by firmware.

### 3.2 FEL mode
- FEL is a BROM USB protocol. It needs a **USB data connection to a host computer**, which is outside the scope of this investigation.
- The F1C200s has **only one USB OTG controller**. The USB-A port on this device is very likely that controller in host mode. FEL through it would need an A-to-A style connection. **That is unsafe without VBUS isolation** because both sides drive 5 V.
- Host tools (`sunxi-fel spiflash-read`, `xfel spinor read`) can read SPI flash this way. This is the **fallback** option, not SD-only.

### 3.3 Existing firmware (WT_RV7186BT_HD, V9.12BT-TP)
- Car-monitor boards based on the F1C200s commonly run **Allwinner Melis (ePDK) RTOS**, not Linux. **This is unconfirmed for this unit.**
- Melis-class devices usually update from TF card through a **vendor-specific** image (often an Allwinner `IMAGEWTY` / PhoenixSuit-style `.img`). File names, folder names and trigger methods (power-on, button, pin-hole) **differ between OEMs**. No WorldTech update package or naming convention was found publicly.
- **No evidence was found** that this firmware has:
  - an SD-card firmware *export* or *dump* function,
  - a diagnostic script interpreter,
  - a shell (Linux shell scripts **must not** be assumed to run).
- These update mechanisms are **write** paths into internal flash. **They are not used or reproduced here.**

### 3.4 Can the existing bootloader read flash and write it to SD?
- Allwinner `boot0` / `boot1` (Melis) loaders read SPI flash into RAM. **No documented function writes flash contents out to SD.**
- So the factory bootloader cannot be relied on for a dump. A dumper would have to be **our own code**, loaded by the BROM from SD (see section 5).

### 3.5 Open-source tools for macOS
| Tool | Purpose | Notes |
|---|---|---|
| `diskutil`, `dd` (built in) | Raw imaging of the SD card | Use `/dev/rdiskN` for speed |
| `shasum -a 256` (built in) | SHA-256 checksums | |
| `hexdump` / `xxd` (built in) | Inspect headers (`eGON.BT0`) | |
| `binwalk` (`brew install binwalk`) | Analyse the dump offline | Read-only analysis |
| Mainline **U-Boot** (`licheepi_nano_defconfig`, `MACH_SUNIV`) | Base for an SD-booted, read-only dumper | Cross-build with `arm-none-eabi-gcc` / `arm-linux-gnueabi-gcc` (Homebrew or Docker) |
| `sunxi-tools` (build from source, needs `libusb`, `dtc`, `pkg-config`) | `mksunxiboot`, `sunxi-fel`, `fel-sdboot.sunxi` | FEL needs USB, so it is fallback only |
| `xfel` (xboot) | FEL tool with F1C100s/F1C200s SPI NOR/NAND read | Fallback only (USB) |
| `flashrom` + CH341A | External SPI read | Fallback hardware |

---

## 4. Confirmed vs unknown

### Confirmed (evidence-based)
- The SoC marking is F1C200s.
- The firmware identity strings match the screenshot (suffix **-TP**).
- The F1C200s BROM is documented to try SDC0 before SPI flash.
- The device has a user-accessible TF slot.

### Unknown (must be resolved before any execution)
1. Whether the **TF slot is wired to SDC0 (PF0–PF5)**. This is the main blocker.
2. The **electrical confirmation of the flash**. The marking says EN25QH64A (8 MiB). Its JEDEC ID (expected `1C 70 17`) has not been read, and its connection to SPI0 (PC0–PC3) has not been traced.
3. Whether any **other non-volatile storage** exists (an I2C EEPROM, or the JieLi BT chip's own flash). The BT chip's firmware is a **separate device** and is not covered by an F1C200s SPI dump.
4. The **OS**: Melis RTOS or something else.
5. Whether settings or calibration are stored in flash or in a separate EEPROM. A complete backup must include any separate EEPROM too.
6. Whether **mainline U-Boot `suniv` SPI and MMC drivers** work on this exact board (pinmux, flash vendor ID support).
7. The board's DRAM clock tolerance (64 MB F1C200s vs the 32 MB F1C100s defaults).
8. The power-on behaviour with a 12 V vehicle harness vs a bench supply.

---

### 4.1 Review of existing repository material (no files changed)

| Existing item | Assessment |
|---|---|
| `docs/HARDWARE.md`: flash = EN25QH64A, 8 MB | **Supported** by `images/crop_flash.png` (marking `QH64A-104HIP` is readable). |
| `docs/HARDWARE.md`: "MicroSD (TF) Slot: Connected to SDC0" | **Not yet backed by measurement.** It is plausible because the F1C200s routes SDC0 to PF0–PF5, but it must be confirmed in Phase 1. Treat it as an assumption. |
| `docs/SD_CARD_DUMP_PROCEDURE.md` | Calls itself "zero-contact" and refers to `tools/prepare_sd_dumper.py`, **which does not exist in the repo**. It also states "64 GB+ SDXC incompatible with BROM" without a source. Treat it as **unverified**; this document supersedes it for feasibility status. |
| `tools/fel-sdboot.bin` (512 B) | The header checks out: `eGON.BT0` magic at offset 4 and length field `0x200`. **Provenance and the FEL entry address for `suniv` are not verified.** Do not write it to a card until it is rebuilt from `linux-sunxi/sunxi-tools` source and compared. Even then, it only helps the USB FEL route, which is outside SD-only scope. |
| `tools/fel_client.py`, `detect_fel.py` | USB FEL host tools. Outside SD-only scope. |

---

## 5. Proposed SD-card-only acquisition workflow (DESIGN ONLY — not built, not deployed)

> [!IMPORTANT]
> This section is a design. **Do not build or deploy any executable until Phase 0 and Phase 1 have passed.**

### How the device would "recognise" the backup process
The device would **not** recognise it at all. The factory firmware is never involved. At power-on, the F1C200s **BROM** reads sector 16 of the SD card. If it finds a valid `eGON.BT0` header and checksum, it loads and runs that code from SD instead of from SPI flash.

### Phase 0: Preserve the original SD card (on the Mac, no device involved)
```sh
diskutil list                                  # identify the card, e.g. /dev/disk4
diskutil unmountDisk /dev/disk4
sudo dd if=/dev/rdisk4 of=original_sd.img bs=1m status=progress
shasum -a 256 original_sd.img > original_sd.img.sha256
```
- Keep the original card unchanged and stored away.
- Use a **separate, spare** card for every later step. Writing an eGON header at the 8 KiB offset would damage the original card's partition layout.

### Phase 1: Non-invasive hardware verification (no code runs)
1. Re-photograph the SOP-8 flash under magnification to confirm `EN25QH64A`. Download the Eon datasheet and record the expected JEDEC ID and capacity (8 MiB).
2. With the device **unpowered**, use a multimeter in continuity mode between the microSD socket pins (CLK, CMD, D0–D3) and the F1C200s pins **PF0–PF5**.
3. Look for UART pads (PE0/PE1, or PA2/PA3 on some boards) for future debugging. Record them only; nothing is needed now.

**Stop condition:** if the TF slot is **not** on SDC0, SD-only extraction is **impossible**. Go to section 7.

### Phase 2: BROM SD-boot proof (optional, minimal)
- Candidate test image: `fel-sdboot.sunxi` from sunxi-tools. It only jumps to FEL and never touches flash.
- Expected result: the device stays dark or blank with the card inserted, then boots normally with the card removed.
- **Open question:** check that its BROM FEL entry address is correct for `suniv` before using it.

### Phase 3: Read-only dumper (to be built only after Phases 1–2 pass)
Base it on mainline U-Boot `licheepi_nano_defconfig`, with these hardening changes:
- `CONFIG_ENV_IS_NOWHERE=y`, so `saveenv` can never write to SPI flash.
- Remove or patch out the `sf write`, `sf erase`, `sf update` and `sf protect` commands, and `mtd` write/erase. Keep `sf probe` and `sf read` only.
- No `CONFIG_CMD_FASTBOOT` and no DFU.
- A built-in, non-interactive `bootcmd` (there is no UART, so no console). Planned logic:
  ```
  sf probe 0
  # Try the largest size first. sf read fails if the size exceeds the detected chip size.
  for size in 0x2000000 0x1000000 0x800000 0x400000:
      sf read 0x80100000 0 $size           -> on success:
      fatwrite mmc 0:1 0x80100000 flash_full_<size>.bin $size
      hash sha256 0x80100000 $size  -> write the hex result to flash_full_<size>.sha256
      sf read 0x82100000 0 $size     (second independent read)
      cmp.b 0x80100000 0x82100000 $size -> write the PASS/FAIL result to readback.txt
      break
  write DONE.txt; then halt (no reset loop, no boot of factory firmware)
  ```
  The 64 MB DRAM easily holds two copies of the 8 MiB EN25QH64A. The size probing above is kept as a guard in case the flash ID turns out to be different.
- If storage turns out to be **SPI NAND**, use `mtd read`, including the OOB/spare area. Page and ECC handling must be planned separately.

### Phase 4: Integrity and completeness verification (on the Mac)
```sh
shasum -a 256 flash_full_*.bin
cat flash_full_*.sha256                         # must match the on-device hash
xxd -l 64 flash_full_*.bin                      # expect "eGON.BT0" at offset 0x4 (boot0 header)
```
A dump may only be labelled **"complete backup"** when **all** of these pass:
1. Dump size equals the capacity from the datasheet / JEDEC ID. For the EN25QH64A, that is **8,388,608 bytes (0x800000)**.
2. The device-side SHA-256 equals the host-side SHA-256.
3. Two independent on-device reads match (`cmp` PASS).
4. Ideally, a **second session** (separate power cycle) gives the same SHA-256.
5. Offset 0 holds a valid boot0 `eGON.BT0` header with a correct checksum.
6. No mirroring: the second half is not a copy of the first half (which would mean the size was over-estimated).
7. Any separate EEPROM (unknown #5) is either dumped too or documented as **excluded**. If it is excluded, the result must be labelled **partial**.

---

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| A buggy dumper sends SPI write/erase commands | **High** | Strip the write/erase/env-save code paths at compile time and review the code before use |
| Corrupting the original SD card | Medium | Phase 0 image plus SHA-256; use a spare card only |
| The TF slot is not on SDC0 | Blocker | Phase 1 continuity check |
| Wrong DRAM timing makes the dumper hang | Low (no flash access) | Power-cycle and remove the card; factory boot is unaffected |
| Accidentally triggering a vendor firmware update | **High** | Spare card contains only the dumper and its outputs, with no vendor update files; never press the pin-hole/reset during power-on |
| "Factory default" pressed by mistake | Medium | Do not open that menu |
| Vehicle power transients during the test | Medium | Bench 12 V supply, with the device out of the car |
| Partial dump mislabelled as complete | Medium | Completeness criteria in Phase 4 |

---

## 7. If SD-only extraction proves impossible: minimum extra hardware

Ranked from least to most invasive:
1. **SOIC-8 test clip + CH341A (3.3 V-modified) or another SPI programmer.** Read in-circuit with `flashrom -p ch341a_spi -r dump.bin` and repeat the read to compare. This is the most common, reliable route and fully read-only. Note: in-circuit reading may back-power the SoC; holding the SoC in reset or lifting the VCC pin may be needed.
2. **USB FEL** (`xfel spinor read` / `sunxi-fel spiflash-read`). Needs a safe USB data link to the SoC's single OTG port, with VBUS isolated.
3. **UART adapter (3.3 V)**. Not needed for dumping, but it greatly lowers risk when running any SD-booted dumper because you can see its output.

---

## 8. Recommended next steps
1. Image the original SD card (Phase 0) and keep the SHA-256.
2. Confirm the EN25QH64A marking with a sharper photo. Then check continuity from the TF socket to PF0–PF5 with the board unpowered.
3. Review this document and update sections 2 and 4 with the results. Also fix the unverified claims in `SD_CARD_DUMP_PROCEDURE.md` (section 4.1).
4. Only then decide between building the Phase 3 read-only dumper or using a SOIC-8 clip read (section 7).

## References
- linux-sunxi wiki: F1C100s / FEL / BROM boot (`linux-sunxi.org`)
- Mainline U-Boot `suniv` support and `licheepi_nano_defconfig`
- `linux-sunxi/sunxi-tools` (GitHub): `sunxi-fel`, `mksunxiboot`, `fel-sdboot`
- `xboot/xfel` (GitHub): F1C100s/F1C200s SPI NOR/NAND read
- Lichee Pi Nano documentation (TF → SPI → FEL boot priority)

