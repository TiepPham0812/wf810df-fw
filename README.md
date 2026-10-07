# Firmware FPT AX3000CV2 (WF-810DF) – ImmortalWrt biên dịch từ mã nguồn

Biên dịch **ImmortalWrt chính hãng** cho **FPT AX3000CV2 bản CV2 (vỏ vuông)** — Actiontec/CIG WF-810DF, Qualcomm IPQ5018 — trên GitHub Actions, không cần máy Linux.

> ⚠️ **Chỉ dành cho CV2 (vỏ vuông).** CV1 (vỏ tròn) dùng phần cứng mạng khác, không nạp bản này.

## Nguồn

- Nền thiết bị (cây thiết bị, driver switch YT9215S, board data Wi-Fi): [zcop/immortalwrt](https://github.com/zcop/immortalwrt/tree/wf810df-25.12) nhánh `wf810df-25.12`.
- Driver YT921x gốc: David Yang (mmyangfl), backport từ Linux 6.19.
- Port ban đầu và hướng dẫn nạp: [michioxd/openwrt-wf810df](https://github.com/michioxd/openwrt-wf810df).
- Thảo luận, phân tích lỗi: [VOZ – OpenWrt cho FPT AX3000CV2](https://voz.vn/t/openwrt-cho-fpt-ax3000cv2-voc.1206194/).

## Khác biệt so với bản michioxd

| | michioxd | Repo này (theo zcop) |
|---|---|---|
| Kết nối switch | MDIO bit-bang, có reset cứng | MDIO1, **bỏ qua reset cứng** |
| Cổng CPU ↔ switch | 2500base-x | **SGMII 1000 Mbps** |
| Hiệu chuẩn 5 GHz | offset `0x4C000` | **`0x26800`** |
| 3 cổng LAN | không lên link | đã chạy trên bản của zcop |
| Treo khi khởi động do driver CMN PLL | có nguy cơ | **đã vá** (bản vá của Stanislaw Pal) |

## Cách build

1. Tab **Actions** → **Build WF810DF - ImmortalWrt tu ma nguon** → **Run workflow**.
2. `iw_ref`: phiên bản ImmortalWrt (vd `v25.12.2`). `extra_packages`: gói thêm (vd `luci-app-sqm wireguard-tools`).
3. Chờ 2–4 giờ. File ở tab **Releases**:
   - `...-squashfs-factory.ubi` — nạp lần đầu
   - `...-initramfs-uImage.itb` — chạy thử trong RAM, không ghi NAND
   - `...-squashfs-sysupgrade.bin` — nâng cấp về sau từ LuCI
   - `kmods-wf810df.tar.gz` — toàn bộ kmod của đúng kernel này

## Cài gói sau khi nạp

- **Gói thường** (luci-app-*, công cụ): `apk update && apk add <gói>` từ kho ImmortalWrt.
- **Gói kmod-\***: kernel tự build nên **không** cài từ kho chính hãng được. Giải nén `kmods-wf810df.tar.gz`, chép `kmod-<tên>*.apk` lên router, chạy `apk add --allow-untrusted /tmp/kmod-<tên>*.apk`.

## Cách nạp

1. **Sao lưu toàn bộ NAND bản gốc trước tiên** — làm theo mục *0. Back up the original firmware* trong [README của michioxd](https://github.com/michioxd/openwrt-wf810df).
2. **Chạy thử trong RAM** (không ghi NAND, rút điện là về như cũ), từ U-Boot:
   ```
   tftpboot 0x44000000 initramfs.itb
   bootm 0x44000000
   ```
   Kiểm tra: 3 cổng LAN lên link, Wi-Fi 2.4/5 GHz phát được, `dmesg | grep -i yt921`.
3. Ổn rồi mới nạp `factory.ubi` theo mục *1. Flash firmware* và *2. Set the startup environment* trong README của michioxd.

## Gợi ý sau khi chạy

- **Packet steering đã bật sẵn**: WAN→LAN từ ~600–700 lên ~940 Mbps theo đo đạc trên VOZ.
- Máy có thể lên **80°C+** khi tải nặng lâu — để nơi thoáng.

## Cảnh báo

Firmware thử nghiệm, chưa được kiểm chứng trên máy thật từ repo này. Tự chịu rủi ro.
