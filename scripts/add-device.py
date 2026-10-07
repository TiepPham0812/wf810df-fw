#!/usr/bin/env python3
"""
Them ho tro FPT AX3000CV2 (WF-810DF, IPQ5018) vao cay nguon ImmortalWrt.

Cach dung:  python3 scripts/add-device.py <thu-muc-nguon-immortalwrt>

- Chep file trong device/ (DTS + ban va driver switch YT921x) vao cay nguon.
- Sua cac file cau hinh chung cua ipq50xx bang cach CHEN them dong,
  khong ghi de ca file -> van giu nguyen cac thiet bi khac cua ImmortalWrt.
- Chay lai nhieu lan van an toan (bo qua neu da them).
- Gap cho nao khong tim thay moc de chen thi DUNG NGAY (exit 1),
  khong de build tiep voi cau hinh thieu.
"""
import os
import re
import shutil
import sys

BOARD = "fpt,ax3000cv2"
DEVICE = "fpt_ax3000cv2"


def die(msg):
    print(f"LOI: {msg}")
    sys.exit(1)


def read(path):
    if not os.path.isfile(path):
        die(f"khong thay file {path}")
    with open(path) as f:
        return f.read()


def write(path, text):
    with open(path, "w") as f:
        f.write(text)


def insert_before(path, text, anchor_regex, block, count=1):
    """Chen block truoc moc anchor_regex (dung count lan dau tien)."""
    m = list(re.finditer(anchor_regex, text, flags=re.M))
    if len(m) < count:
        die(f"{path}: khong tim thay moc '{anchor_regex}'")
    out = text
    for match in reversed(m[:count]):
        out = out[: match.start()] + block + out[match.start():]
    return out


def main():
    if len(sys.argv) != 2:
        die("can 1 tham so: thu muc nguon ImmortalWrt")
    src = os.path.abspath(sys.argv[1])
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Chep DTS + ban va kernel
    dev = os.path.join(repo, "device")
    for root, _, files in os.walk(dev):
        for name in files:
            s = os.path.join(root, name)
            d = os.path.join(src, os.path.relpath(s, dev))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            print(f"chep  {os.path.relpath(d, src)}")

    q = os.path.join(src, "target/linux/qualcommax")

    # 2. Khai bao image (Makefile ipq50xx)
    p = os.path.join(q, "image/ipq50xx.mk")
    t = read(p)
    if f"define Device/{DEVICE}" not in t:
        for need in ("define Device/FitImage", "define Device/UbiFit"):
            if need not in read(os.path.join(q, "image/Makefile")):
                die(f"image/Makefile thieu {need}")
        t = t.rstrip("\n") + f"""

define Device/{DEVICE}
	$(call Device/FitImage)
	$(call Device/UbiFit)
	DEVICE_VENDOR := FPT
	DEVICE_MODEL := AX3000CV2
	DEVICE_ALT0_VENDOR := Actiontec
	DEVICE_ALT0_MODEL := WF-810DF
	SOC := ipq5018
	BLOCKSIZE := 128k
	PAGESIZE := 2048
	NAND_SIZE := 256m
	UBINIZE_OPTS := -E 5
	DEVICE_PACKAGES := ath11k-firmware-ipq5018-qcn6122 \\
		kmod-gpio-pwm kmod-leds-pwm kmod-mdio-gpio
endef
TARGET_DEVICES += {DEVICE}
"""
        write(p, t)
        print("sua   image/ipq50xx.mk")

    # 3. Cau hinh cong mang: lan1-3 + wan
    p = os.path.join(q, "ipq50xx/base-files/etc/board.d/02_network")
    t = read(p)
    if BOARD not in t:
        t = insert_before(p, t, r"^\tesac\n\}",
                          f'\t{BOARD})\n\t\tucidef_set_interfaces_lan_wan "lan1 lan2 lan3" "wan"\n\t\t;;\n')
        write(p, t)
        print("sua   board.d/02_network")

    # 4. Du lieu hieu chuan Wi-Fi tu phan vung ART + MAC tu APPSBLENV
    p = os.path.join(q, "ipq50xx/base-files/etc/hotplug.d/firmware/11-ath11k-caldata")
    t = read(p)
    if BOARD not in t:
        blocks = {
            r'"ath11k/IPQ5018/hw1\.0/cal-ahb-c000000\.wifi\.bin"\)\n\tcase "\$board" in\n':
                f'\t{BOARD})\n\t\tcaldata_extract "0:ART" 0x1000 0x20000\n'
                f'\t\tlabel_mac=$(mtd_get_mac_ascii 0:APPSBLENV ethaddr)\n'
                f'\t\tath11k_patch_mac $label_mac 0\n\t\tath11k_set_macflag\n\t\t;;\n',
            r'"ath11k/QCN6122/hw1\.0/cal-ahb-b00a040\.wifi\.bin"\)\n\tcase "\$board" in\n':
                f'\t{BOARD})\n\t\tcaldata_extract "0:ART" 0x4C000 0x20000\n'
                f'\t\tlabel_mac=$(mtd_get_mac_ascii 0:APPSBLENV ethaddr)\n'
                f'\t\tath11k_patch_mac $(macaddr_add $label_mac 2) 0\n\t\tath11k_set_macflag\n\t\t;;\n',
        }
        for anchor, block in blocks.items():
            m = re.search(anchor, t)
            if not m:
                die(f"{p}: khong tim thay moc {anchor}")
            t = t[: m.end()] + block + t[m.end():]
        write(p, t)
        print("sua   hotplug.d/firmware/11-ath11k-caldata")

    # 5. Nang cap (sysupgrade): dung chung kieu voi zyxel,scr50axe
    p = os.path.join(q, "ipq50xx/base-files/lib/upgrade/platform.sh")
    t = read(p)
    if BOARD not in t:
        if "\tzyxel,scr50axe)\n\t\tCI_UBIPART=\"rootfs\"" not in t:
            die(f"{p}: khoi zyxel,scr50axe da doi, can xem lai")
        t = t.replace("\tzyxel,scr50axe)\n\t\tCI_UBIPART=\"rootfs\"",
                      f"\tzyxel,scr50axe|\\\n\t{BOARD})\n\t\tCI_UBIPART=\"rootfs\"", 1)
        write(p, t)
        print("sua   lib/upgrade/platform.sh")

    # 6. fw_printenv/fw_setenv: dung chung kieu voi glinet,gl-b3000
    p = os.path.join(src, "package/boot/uboot-tools/uboot-envtools/files/qualcommax_ipq50xx")
    t = read(p)
    if BOARD not in t:
        if "glinet,gl-b3000)\n" not in t:
            die(f"{p}: khong thay glinet,gl-b3000")
        t = t.replace("glinet,gl-b3000)\n", f"glinet,gl-b3000|\\\n{BOARD})\n", 1)
        write(p, t)
        print("sua   uboot-envtools/qualcommax_ipq50xx")

    # 7. Cau hinh kernel: driver switch YT921x + MDIO bit-bang
    def set_cfg(path, keys):
        t = read(path)
        for k in keys:
            t = re.sub(rf"^# {k} is not set\n", "", t, flags=re.M)
            if not re.search(rf"^{k}=y$", t, flags=re.M):
                t = t.rstrip("\n") + f"\n{k}=y\n"
        write(path, t)
        print(f"sua   {os.path.relpath(path, src)}")

    set_cfg(os.path.join(q, "ipq50xx/config-default"),
            ["CONFIG_NET_DSA_YT921X", "CONFIG_NET_DSA_TAG_YT921X"])
    # 2 tuy chon phu cua driver: tat, khai bao ro de kernel khong hoi khi build
    p = os.path.join(q, "ipq50xx/config-default")
    t = read(p)
    for k in ("CONFIG_NET_DSA_YT921X_DEBUG", "CONFIG_NET_DSA_YT921X_CR881X"):
        if k not in t:
            t = t.rstrip("\n") + f"\n# {k} is not set\n"
    write(p, t)
    set_cfg(os.path.join(q, "config-6.12"),
            ["CONFIG_MOTORCOMM_PHY", "CONFIG_MDIO_GPIO"])

    print("XONG: da them FPT AX3000CV2 vao", src)


if __name__ == "__main__":
    main()
