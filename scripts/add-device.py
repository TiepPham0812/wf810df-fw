#!/usr/bin/env python3
"""
Them ho tro FPT AX3000CV2 (Actiontec WF-810DF, IPQ5018) vao cay nguon ImmortalWrt.

Cach dung:  python3 scripts/add-device.py <thu-muc-nguon-immortalwrt>

Nen tang thiet bi lay tu zcop/immortalwrt nhanh wf810df-25.12 (LAN + Wi-Fi da
bring-up, xac nhan tren VOZ): DTS ipq5018-wf810df, driver switch YT921x
(backport v6.19 + 2 ban hack: SGMII/REVSGMII va bo qua reset cung).

- Chep file trong device/ vao cay nguon.
- Sua cac file chung cua ipq50xx bang cach CHEN them, khong ghi de ca file.
- Chay lai nhieu lan van an toan.
- Khong tim thay moc de chen thi DUNG NGAY (exit 1).
"""
import os
import re
import shutil
import sys

BOARDS = ["fpt,ax3000cv2", "fpt,wf810df"]      # board_name co the la 1 trong 2
CASE = "|\\\n\t".join(BOARDS)                  # "fpt,ax3000cv2|\\\n\tfpt,wf810df"
DEVICE = "wf810df"


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


def main():
    if len(sys.argv) != 2:
        die("can 1 tham so: thu muc nguon ImmortalWrt")
    src = os.path.abspath(sys.argv[1])
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    q = os.path.join(src, "target/linux/qualcommax")

    # 1. Chep DTS + ban va kernel
    dev = os.path.join(repo, "device")
    for root, _, files in os.walk(dev):
        for name in files:
            s = os.path.join(root, name)
            d = os.path.join(src, os.path.relpath(s, dev))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            print(f"chep  {os.path.relpath(d, src)}")

    # 2. Goi kmod-dsa-yt921x (driver switch dang module)
    p = os.path.join(src, "package/kernel/linux/modules/netdevices.mk")
    t = read(p)
    if "KernelPackage/dsa-yt921x" not in t:
        t = t.rstrip("\n") + """


define KernelPackage/dsa-yt921x
  SUBMENU:=$(NETWORK_DEVICES_MENU)
  TITLE:=Motorcomm YT921x DSA switch support
  DEPENDS:=+kmod-dsa
  KCONFIG:= \\
	CONFIG_NET_DSA_YT921X \\
	CONFIG_NET_DSA_TAG_YT921X
  FILES:= \\
	$(LINUX_DIR)/drivers/net/dsa/yt921x.ko \\
	$(LINUX_DIR)/net/dsa/tag_yt921x.ko
  AUTOLOAD:=$(call AutoLoad,30,tag_yt921x yt921x)
endef

define KernelPackage/dsa-yt921x/description
 Kernel module for Motorcomm YT9215/YT9218 DSA switch and tag protocol
endef

$(eval $(call KernelPackage,dsa-yt921x))
"""
        if "define KernelPackage/dsa\n" not in t:
            die("netdevices.mk khong co kmod-dsa")
        write(p, t)
        print("sua   netdevices.mk (kmod-dsa-yt921x)")

    # 3. Khai bao image. DEVICE_DTS_CONFIG de U-Boot goc (bootipq) chon dung cau hinh.
    #    Board data Wi-Fi nam o files/ nen khong dung ipq-wifi-wf810df.
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
	DEVICE_DTS := ipq5018-wf810df
	DEVICE_DTS_CONFIG := config@mp03.3-c3
	DEVICE_VENDOR := FPT
	DEVICE_MODEL := AX3000CV2
	DEVICE_ALT0_VENDOR := Actiontec
	DEVICE_ALT0_MODEL := WF810DF
	SUPPORTED_DEVICES += fpt,wf810df fpt_ax3000cv2 fpt,ax3000cv2 actiontec,wf810df
	SOC := ipq5018
	BLOCKSIZE := 128k
	PAGESIZE := 2048
	NAND_SIZE := 256m
	UBINIZE_OPTS := -E 5
	DEVICE_PACKAGES := ath11k-firmware-ipq5018-qcn6122 \\
		kmod-dsa-yt921x kmod-mdio-gpio
endef
TARGET_DEVICES += {DEVICE}
"""
        write(p, t)
        print("sua   image/ipq50xx.mk")

    # 4. Cong mang: lan1-3 + wan
    p = os.path.join(q, "ipq50xx/base-files/etc/board.d/02_network")
    t = read(p)
    if BOARDS[0] not in t:
        m = re.search(r"^\tesac\n\}", t, flags=re.M)
        if not m:
            die(f"{p}: khong tim thay moc esac")
        block = f'\t{CASE})\n\t\tucidef_set_interfaces_lan_wan "lan1 lan2 lan3" "wan"\n\t\t;;\n'
        t = t[: m.start()] + block + t[m.start():]
        write(p, t)
        print("sua   board.d/02_network")

    # 5. Hieu chuan Wi-Fi tu ART. 5 GHz = 0x26800 (zcop + greenhope sua tu 0x4C000).
    p = os.path.join(q, "ipq50xx/base-files/etc/hotplug.d/firmware/11-ath11k-caldata")
    t = read(p)
    if BOARDS[0] not in t:
        blocks = {
            r'"ath11k/IPQ5018/hw1\.0/cal-ahb-c000000\.wifi\.bin"\)\n\tcase "\$board" in\n':
                f'\t{CASE})\n\t\tcaldata_extract "0:ART" 0x1000 0x20000\n'
                f'\t\tlabel_mac=$(mtd_get_mac_ascii 0:APPSBLENV ethaddr)\n'
                f'\t\tath11k_patch_mac $label_mac 0\n\t\tath11k_set_macflag\n\t\t;;\n',
            r'"ath11k/QCN6122/hw1\.0/cal-ahb-b00a040\.wifi\.bin"\)\n\tcase "\$board" in\n':
                f'\t{CASE})\n\t\tcaldata_extract "0:ART" 0x26800 0x20000\n'
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

    # 6. sysupgrade: dung chung kieu voi zyxel,scr50axe
    p = os.path.join(q, "ipq50xx/base-files/lib/upgrade/platform.sh")
    t = read(p)
    if BOARDS[0] not in t:
        old = "\tzyxel,scr50axe)\n\t\tCI_UBIPART=\"rootfs\""
        if old not in t:
            die(f"{p}: khoi zyxel,scr50axe da doi, can xem lai")
        t = t.replace(old, f"\tzyxel,scr50axe|\\\n\t{CASE})\n\t\tCI_UBIPART=\"rootfs\"", 1)
        write(p, t)
        print("sua   lib/upgrade/platform.sh")

    # 7. fw_printenv/fw_setenv
    p = os.path.join(src, "package/boot/uboot-tools/uboot-envtools/files/qualcommax_ipq50xx")
    t = read(p)
    if BOARDS[0] not in t:
        if "glinet,gl-b3000)\n" not in t:
            die(f"{p}: khong thay glinet,gl-b3000")
        t = t.replace("glinet,gl-b3000)\n",
                      "glinet,gl-b3000|\\\n" + "|\\\n".join(BOARDS) + ")\n", 1)
        write(p, t)
        print("sua   uboot-envtools/qualcommax_ipq50xx")

    print("XONG: da them FPT AX3000CV2 (wf810df) vao", src)


if __name__ == "__main__":
    main()
