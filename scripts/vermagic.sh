#!/bin/bash
# Tinh truoc vermagic cua kernel (khong can toolchain, chay ngay sau make defconfig).
# Lam giong het include/kernel-defaults.mk (Kernel/Configure/Default), ke ca viec
# BO QUA cac dong YT921X ma buoc 6c da chen vao kernel-defaults.mk.
#
# Dung: scripts/vermagic.sh <thu-muc-nguon-immortalwrt> [thu-muc-ra]
# In ra: <hash vermagic>. File .config.set de o thu muc ra (mac dinh <nguon>/tmp/vermagic).
set -euo pipefail
T=$(cd "$1" && pwd); O=${2:-$T/tmp/vermagic}; mkdir -p "$O"
# Dong kernel bi bo khoi vermagic: driver switch YT921x (chi rieng 810, chi them module)
EXCLUDE='^CONFIG_NET_DSA(_TAG)?_YT921X='
mk() { make -s -C "$T/target/linux/$(sed -n 's/^CONFIG_TARGET_BOARD="\(.*\)"/\1/p' "$T/.config")" TOPDIR="$T" "val.$1"; }
CMD=$(mk LINUX_CONF_CMD); PATCHVER=$(mk KERNEL_PATCHVER)
[ -n "$CMD" ] && [ -n "$PATCHVER" ] || { echo "LOI: khong lay duoc LINUX_CONF_CMD/KERNEL_PATCHVER" >&2; exit 1; }
test -s "$T/tmp/.packageinfo" || { echo "LOI: chua chay make defconfig" >&2; exit 1; }
$CMD > "$O/.config.target"
awk '/^(#[[:space:]]+)?CONFIG_KERNEL/{sub("CONFIG_KERNEL_","CONFIG_");print}' "$T/.config" >> "$O/.config.target"
{
	echo "# CONFIG_KALLSYMS_EXTRA_PASS is not set"
	echo "# CONFIG_KALLSYMS_ALL is not set"
	echo "CONFIG_KALLSYMS_UNCOMPRESSED=y"
} >> "$O/.config.target"
"$T/scripts/package-metadata.pl" kconfig "$T/tmp/.packageinfo" "$T/.config" "$PATCHVER" > "$O/.config.override"
"$T/scripts/kconfig.pl" 'm+' '+' "$O/.config.target" /dev/null "$O/.config.override" > "$O/.config.set"
grep '=[ym]' "$O/.config.set" | grep -v -E "$EXCLUDE" | LC_ALL=C sort > "$O/vermagic-input.txt"
md5sum < "$O/vermagic-input.txt" | cut -d' ' -f1
