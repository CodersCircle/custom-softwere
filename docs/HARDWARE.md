# Hardware Analysis: WorldTech WT-RV7186BT

## 1. System Overview

The **WorldTech WT-RV7186BT** is an aftermarket automotive smart rearview mirror monitor featuring a touchscreen LCD, media playback from USB/MicroSD, Bluetooth hands-free audio, dual AV inputs for rearview/dash cameras, and FM audio transmission to the car stereo.

---

## 2. Component Identification

### 2.1 Main SoC (System on Chip)
- **Marking**:
  ```
  ALLWINNER TECH
  F1C200s
  M90298B 69J2
  ```
- **Package**: QFN88 (88-pin Quad Flat No-leads, 0.4 mm pitch, e-pad)
- **Architecture**: ARM926EJ-S core (ARMv5TEJ instruction set)
- **Clock**: Up to ~720 MHz (default ~408–533 MHz)
- **Internal RAM**: **64 MB DDR1 SDRAM built-in** (System-in-Package, SIP)
- **Caches**: 16 KB D-Cache, 32 KB I-Cache
- **Peripherals**:
  - Video Engine: H.264 / MPEG-1/2/4 / JPEG / MJPEG hardware decoder (up to 720p/1080p)
  - Display Interface: 24-bit RGB parallel LCD interface
  - Video Input: Integrated TV CVBS decoder (supports NTSC/PAL analog camera inputs)
  - Audio: Integrated 24-bit audio DAC and ADC
  - USB: USB 2.0 High-Speed OTG controller
  - Storage: SDC0 / SDC1 (SD/MMC controllers)
  - Bus Interfaces: SPI0, SPI1, TWI0, TWI1, UART0, UART1, UART2, PWM, CIR, LRADC (Key ADC)
- **Main Oscillator**: External 24.000 MHz quartz crystal (`X24.000`)

### 2.2 Flash Memory (Firmware Storage)
- **Marking**:
  ```
  cFeon
  QH64-104HIP
  U102303
  2140HSA
  ```
- **Manufacturer**: Eon Silicon Solution (cFeon / Chingis)
- **Part Number**: `EN25QH64A` / `EN25QH64-104HIP`
- **Memory Type**: High-speed SPI NOR Flash memory
- **Density**: 64 Megabits = **8 Megabytes (8,388,608 bytes)**
- **Operating Voltage**: 2.7 V to 3.6 V (Nominal **3.3 V**)
- **Max Frequency**: 104 MHz (Dual/Quad SPI supported)
- **Package**: SOP-8 (SOIC-8 208-mil)
- **Pinout (Standard JEDEC SOIC-8)**:
  ```
           +---v---+
     /CS  1|       |8  VCC (3.3V)
  SO/IO1  2|       |7  /HOLD / IO3
 /WP/IO2  3|       |6  SCLK
     GND  4|       |5  SI / IO0
           +-------+
  ```

### 2.3 Secondary Microcontrollers & Peripheral ICs
1. **Bluetooth Subsystem**:
   - Marking: `JL AC21BP0A906-504` (JieLi Technology AC21 series Bluetooth audio SoC)
   - Function: Handles Bluetooth A2DP audio streaming, hands-free calling (HFP), and AVRCP control.
   - Clock: Dedicated 24 MHz crystal.
   - RF: Connected to on-board PCB inverted-F antenna marked `BT-ANT`.
2. **Audio Power Amplifier**:
   - Marking: `8002D / XS2180B` (8-pin SOP)
   - Function: Class AB 3W mono bridge-tied load (BTL) audio power amplifier driving the internal speaker/piezo.
3. **FM Radio Transmitter**:
   - Marking: 10-pin TSSOP/MSOP IC near bottom-right edge.
   - Function: FM audio broadcast to the vehicle's head unit.
   - RF: Connected to dedicated test point / line marked `FM-ANT`.
4. **Power Regulation Section**:
   - Inductor and electrolytic filter capacitors (330 µF / 6.3V, 100 µF / 25V, 220 µF) with step-down switching regulator (likely buck converter stepping 12V automotive input down to 5V and 3.3V/1.2V rails for the SoC and peripherals).

---

## 3. PCB Connectors, Headers, and Test Points

### 3.1 External Ports (Top Casing Edge)
1. **AV-IN 1**: 2.5 mm / 3.5 mm jack (Auxiliary composite video/audio input)
2. **AV-IN 2 / Camera**: Jack for rearview reversing camera trigger/feed
3. **USB-A Port**: Female Type-A USB socket (typically media playback from flash drives; potentially routed to F1C200s USB OTG controller)
4. **MicroSD (TF) Slot**: Connected to SDC0 of F1C200s (Media playback / firmware updates / bootloader recovery)
5. **Microphone / Reset Holes**: Pinhole openings for electret mic and tactile reset/power indication

### 3.2 Internal Board Headers & Silk Markings
- **Bottom-Left Header Pads**:
  - `3.3V`: 3.3 V DC power supply rail
  - `GND`: System ground
  - `IRIN`: Infrared remote control sensor receiver input
  - `KEY0`: Analog resistor ladder key / push button input (LRADC)
  - `LED`: Status LED control line
- **Display Ribbon Connectors**:
  - Wide FPC connector (40-pin or 50-pin standard RGB parallel interface for the LCD panel)
  - Smaller FPC connector (touch panel digitizer interface: I2C or 4-wire resistive)
- **Main Power / Harness Connector (Right Edge)**:
  - Multi-pin shrouded latching JST header carrying +12V battery power, +12V accessory (ACC), ground, reverse signal trigger, and camera video lines.
- **Test Points**:
  - `MHL`: Round test point near F1C200s
  - `BT-ANT`: Bluetooth antenna feed point
  - `FM-ANT`: FM transmitter antenna feed point
  - Row of test vias located between F1C200s and top connector (candidates for UART0 TX/RX).

---

## 4. Hardware Interfaces & Risk Evaluation

| Interface | Potential Capability | Safe Extraction Role | Risk Level | Safety Instruction |
| :--- | :--- | :--- | :--- | :--- |
| **cFeon EN25QH64A SPI** | Direct SPI Read | Primary backup target (using 3.3V programmer + SOIC-8 clip) | **Low** (when unpowered) | Ensure host device is completely powered down. Verify programmer is set to 3.3V (NOT 5V). |
| **MicroSD (SDC0)** | BROM Boot Priority | Secondary backup method (boot custom dumper payload) | **Very Low** | Safe, purely non-invasive; read-only to onboard flash. |
| **USB-A Port** | USB Host / OTG FEL | Potential FEL mode recovery interface | **Medium** | Do NOT connect directly to host Mac until pinout and VBUS voltage are verified with DMM. USB-A ports on car monitors frequently carry 5V or vehicle power out. |
| **UART0 Console** | Serial Debug Logging | Diagnostic log observation (boot messages, shell) | **Low** | Use 3.3V FTDI / CP2102 adapter with RX/TX only. Do NOT connect power pins. |
