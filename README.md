# WorldTech WT-RV7186BT Firmware Reverse Engineering

## Project Overview
Reverse engineering and custom software development for the **WorldTech WT-RV7186BT** automotive touchscreen rearview mirror display monitor.

---

## Device Summary

| Parameter | Confirmed Value |
| :--- | :--- |
| **Device Model** | WorldTech WT-RV7186 / WT-RV7186BT (Marked `WT-RV7185BT HD/22` on bezel) |
| **Main SoC** | **Allwinner F1C200s** (ARM926EJ-S @ up to ~720 MHz, 64MB SIP DDR1) |
| **PCB Designation** | `WT-RV7186-TOUCH_V1.1` (Silkscreen date code: `2144`) |
| **Flash Memory** | **cFeon (Eon) EN25QH64A** (`QH64-104HIP`) - 64 Mbit (8 MByte) SPI NOR Flash |
| **Bluetooth Subsystem**| JieLi AC21 series (`AC21BP0A906-504`) with dedicated 24 MHz crystal & PCB antenna |
| **Audio Amplifier** | 8002D / XS2180B 3W audio power amplifier |
| **FM Transmitter** | Dedicated FM transmitter IC with `FM-ANT` antenna output |
| **Firmware Version** | `V9.12BT-TP` (Reported in system UI) |
| **Firmware Info / ID** | `WT_RV7186BT_HD` |
| **Firmware Build Date**| `2021.12.13` |
| **Display & Touch** | High-definition LCD panel with resistive/capacitive touch digitizer overlay |

---

## Repository Structure

```
├── README.md                  # This file
├── docs/
│   ├── HARDWARE.md            # Hardware analysis, IC identifications, and pinouts
│   └── FIRMWARE_BACKUP_PLAN.md# Step-by-step, read-only extraction & safety plan
├── images/                    # Reference PCB, device casing, and UI photographs
└── tools/                     # Scripts and configuration files (to be added)
```

---

## Safety Guidelines

1. **Non-Destructive First**: Never perform write, erase, flash, or reset operations until full, verified backups exist.
2. **Read-Only Verification**: All flash memory dumps must be verified with matching SHA-256 hashes across independent reads.
3. **Voltage Safety**: All logic levels on the Allwinner F1C200s and cFeon SPI Flash are **3.3V**. Never apply 5V logic or power to SPI/UART lines.
4. **USB Port Caution**: Do not assume the top USB-A port is a standard USB OTG device port without measuring VBUS and line traces.

---

## Quick Reference Links
- Detailed Hardware Breakdown: [docs/HARDWARE.md](docs/HARDWARE.md)
- Firmware Backup Plan: [docs/FIRMWARE_BACKUP_PLAN.md](docs/FIRMWARE_BACKUP_PLAN.md)
