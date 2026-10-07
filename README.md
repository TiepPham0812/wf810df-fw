# Firmware FPT AX3000CV2 (WF-810DF) – ImmortalWrt biên dịch từ mã nguồn

Biên dịch **ImmortalWrt chính hãng** cho **FPT AX3000CV2** (Actiontec/CIG WF-810DF, Qualcomm IPQ5018) trên GitHub Actions, không cần máy Linux.

Phần hỗ trợ thiết bị (cây thiết bị, driver switch YT921x, cấu hình) lấy từ [michioxd/openwrt-wf810df](https://github.com/michioxd/openwrt-wf810df) — cảm ơn michioxd và zcop. Dữ liệu Wi-Fi `board-2.bin` lấy từ [michioxd/upstream-wifi-fw](https://github.com/michioxd/upstream-wifi-fw).

## Trạng thái phần cứng

| Thành phần | Trạng thái |
|---|---|
| WAN (cổng nội của IPQ5018) | ✅ |
| Wi-Fi 2.4 GHz / 5 GHz (QCN6102) | ✅ |
| NAND, nút Reset/WPS | ✅ |
| **3 cổng LAN (switch YT9215S)** | ❌ nhận chip nhưng chưa lên link |
| NSS (tăng tốc phần cứng) | ❌ |

→ Hiện dùng được như **router Wi-Fi 1 cổng WAN**.

## Cách build

1. Tab **Actions** → **Build WF810DF - ImmortalWrt tu ma nguon** → **Run workflow**.
2. `iw_ref`: phiên bản ImmortalWrt (vd `v25.12.2`). `extra_packages`: gói thêm (vd `luci-app-sqm wireguard-tools`).
3. Chờ 2–4 giờ. File ở tab **Releases**:
   - `...-squashfs-factory.ubi` — nạp lần đầu qua U-Boot
   - `...-initramfs-uImage.itb` — chạy thử trong RAM, không ghi NAND
   - `...-squashfs-sysupgrade.bin` — nâng cấp về sau từ LuCI
   - `kmods-wf810df.tar.gz` — toàn bộ kmod của đúng kernel này

## Cài gói sau khi nạp

- **Gói thường** (luci-app-*, công cụ): `apk update && apk add <gói>` — lấy từ kho ImmortalWrt.
- **Gói kmod-\***: kernel tự build nên **không** cài được từ kho chính hãng. Giải nén `kmods-wf810df.tar.gz`, chép file `kmod-<tên>*.apk` lên router rồi `apk add --allow-untrusted /tmp/kmod-<tên>*.apk`.

## Cách nạp

**Bắt buộc trước tiên: UART + sao lưu toàn bộ NAND bản gốc** — làm đúng mục *0. Back up the original firmware* trong [README của michioxd](https://github.com/michioxd/openwrt-wf810df#0-back-up-the-original-firmware-dump-the-entire-nand).

**Nên chạy thử trong RAM trước** (không ghi gì vào NAND, rút điện là về như cũ):
```
tftpboot 0x44000000 initramfs.itb
bootm 0x44000000
```

Nạp thật: làm theo mục *1. Flash firmware* và *2. Set the startup environment* trong README của michioxd, dùng file `factory.ubi` từ Releases của repo này.

## Cảnh báo

Firmware thử nghiệm, chỉ dành cho người có UART và đã sao lưu NAND. Tự chịu rủi ro.
