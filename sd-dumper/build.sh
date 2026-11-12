#!/usr/bin/env bash
# Builds a READ-ONLY U-Boot SD-card dumper for the F1C200s (suniv).
# Every hardening step is verified; the build FAILS if any check fails.
set -euo pipefail

UBOOT_TAG="${UBOOT_TAG:-v2024.10}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/out"
mkdir -p "$OUT"
export ARCH=arm CROSS_COMPILE=arm-linux-gnueabi-

rm -rf /tmp/u-boot
git clone --depth 1 --branch "$UBOOT_TAG" https://github.com/u-boot/u-boot.git /tmp/u-boot
cd /tmp/u-boot

echo "=== HARDENING 1: Write-Enable (0x06) opcode replaced with Read-Status (0x05) ==="
# Without WREN the flash chip itself ignores every program / erase / status-register write.
H=include/linux/mtd/spi-nor.h
grep -nE 'define[[:space:]]+SPINOR_OP_WREN[[:space:]]+0x06' "$H"
sed -i -E 's/(define[[:space:]]+SPINOR_OP_WREN[[:space:]]+)0x06/\10x05 \/* READ-ONLY DUMPER: WREN disabled *\//' "$H"
grep -nE 'define[[:space:]]+SPINOR_OP_WREN[[:space:]]+0x05' "$H"
# Any other write-enable opcode definition or literal use in SPI flash code => abort.
if grep -rnE '(WREN|WRITE_ENABLE)[A-Z_]*[[:space:]]+0x06|SPI_MEM_OP_CMD\(0x06' drivers/mtd/spi drivers/spi include/linux/mtd arch/arm/mach-sunxi; then
  echo "FATAL: other write-enable definitions found"; exit 1
fi

echo "=== HARDENING 2: 'sf' command limited to probe/read ==="
python3 - <<'PY'
import re
p = "cmd/sf.c"
s = open(p).read()
needle = "\tcmd = argv[1];\n"
assert s.count(needle) == 1, "sf.c layout changed"
s = s.replace(needle, needle +
  '\tif (strcmp(cmd, "probe") && strcmp(cmd, "read")) {\n'
  '\t\tprintf("READ-ONLY DUMPER: sf %s blocked\\n", cmd);\n'
  '\t\treturn CMD_RET_FAILURE;\n\t}\n')
open(p, "w").write(s)
PY
grep -n "READ-ONLY DUMPER" cmd/sf.c

echo "=== CONFIG ==="
make licheepi_nano_defconfig
C=./scripts/config
$C -e ENV_IS_NOWHERE -d ENV_IS_IN_SPI_FLASH -d ENV_IS_IN_FAT -d ENV_IS_IN_MMC -d ENV_IS_IN_EXT4
$C -d SPI_FLASH_UNLOCK_ALL -d CMD_SPI -d CMD_MTD -d CMD_SF_TEST -d SPI_FLASH_SFDP_SUPPORT -d CMD_SAVEENV
$C -e SPI -e DM_SPI -e SPI_SUNXI -e SPI_FLASH -e DM_SPI_FLASH -e SPI_FLASH_EON -e CMD_SF
$C -e MMC -e MMC_WRITE -e CMD_MMC -e CMD_FAT -e FS_FAT -e FAT_WRITE -e CMD_HASH -e HASH_VERIFY -e SHA256 -e CMD_MEMORY -e CMD_EXPORTENV
$C -e USE_DEFAULT_ENV_FILE --set-str DEFAULT_ENV_FILE "$HERE/dumper.env"
$C --set-val BOOTDELAY -2
make olddefconfig

fail=0
for s in ENV_IS_NOWHERE SPI_SUNXI DM_SPI_FLASH SPI_FLASH_EON CMD_SF FAT_WRITE CMD_HASH SHA256 USE_DEFAULT_ENV_FILE MMC_WRITE; do
  grep -q "^CONFIG_${s}=y" .config || { echo "MISSING: CONFIG_${s}"; fail=1; }
done
for s in SPI_FLASH_UNLOCK_ALL ENV_IS_IN_SPI_FLASH CMD_SPI CMD_MTD CMD_SF_TEST; do
  if grep -q "^CONFIG_${s}=y" .config; then echo "FORBIDDEN ENABLED: CONFIG_${s}"; fail=1; fi
done
[ "$fail" = 0 ] || exit 1

echo "=== BUILD ==="
make -j"$(nproc)"

echo "=== VERIFY OUTPUT ==="
BIN=u-boot-sunxi-with-spl.bin
SIZE=$(stat -c %s "$BIN")
echo "size=$SIZE"
[ "$SIZE" -lt 1040384 ] || { echo "FATAL: too large for 8KiB..1MiB gap"; exit 1; }
head -c 16 "$BIN" | od -A x -t x1z | head -2
head -c 12 "$BIN" | tail -c 8 | grep -q "eGON.BT0" || { echo "FATAL: no eGON.BT0 header"; exit 1; }
dtc -I dtb -O dts u-boot.dtb 2>/dev/null > "$OUT/u-boot.dts"
grep -q "jedec,spi-nor" "$OUT/u-boot.dts" || { echo "FATAL: no SPI NOR node in device tree"; exit 1; }
grep -q "sun.*mmc\|suniv.*mmc" "$OUT/u-boot.dts" || { echo "FATAL: no MMC node in device tree"; exit 1; }
strings u-boot.bin | grep -q "dump_all" || { echo "FATAL: dumper env not embedded"; exit 1; }

cp "$BIN" "$OUT/"
cp .config "$OUT/uboot.config"
( cd "$OUT" && sha256sum "$BIN" > "$BIN.sha256" )
echo "UBOOT_TAG=$UBOOT_TAG" > "$OUT/BUILD_INFO.txt"
echo "BUILD OK"
