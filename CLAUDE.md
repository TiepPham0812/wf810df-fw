# Quy tắc dự án wf810df-fw

## Mục tiêu
- Firmware **ImmortalWrt biên dịch từ mã nguồn chính hãng** cho **FPT AX3000CV2 bản CV2 (vỏ vuông)** — Actiontec/CIG WF-810DF, Qualcomm IPQ5018 + QCN6102, switch Motorcomm YT9215S.
- Không dùng cho CV1 (vỏ tròn, khác PHY).
- Nền thiết bị lấy từ **`zcop/immortalwrt` nhánh `wf810df-25.12`** (LAN và Wi-Fi đã bring-up, xác nhận trên thread VOZ). Không fork nguyên cây nguồn.
- NSS chưa có (chỉ có ở hướng kernel QSDK 5.4, không ghép được).

## Cấu trúc
- `device/` — chép thẳng vào cây nguồn:
  - DTS `ipq5018-wf810df.dts` (switch qua MDIO1, `motorcomm,skip-hw-reset`, cổng CPU `sgmii` cố định 1000 Mbps)
  - `backport-6.12/830-01`, `830-02`: driver YT921x (backport v6.19)
  - `hack-6.12/940`: dùng SGMII thay REVSGMII; `941`: tuỳ chọn DT bỏ qua reset cứng
  - `qualcommax/patches-6.12/0199`: chống treo IPQ5018 do CMN PLL
- `scripts/add-device.py` — thêm gói `kmod-dsa-yt921x`, khai báo image `wf810df`, chèn thiết bị vào 02_network, caldata, platform.sh, uboot-env. Chỉ chèn thêm; không tìm thấy mốc thì dừng.
- `files/` — chép vào firmware: `board-2.bin` Wi-Fi (từ zcop), múi giờ VN.
- `config/wf810df.seed` — cấu hình gói.
- `.github/workflows/build-wf810df.yml` — tải ImmortalWrt theo tag, ghép thiết bị, build (2–4 giờ).

## Những điểm đã có bằng chứng — KHÔNG đổi lại
- **Không reset cứng switch** và **không dùng `2500base-x`** cho cổng CPU: reset xoá thanh ghi U-Boot đã cấu hình → LAN mất link; 2500base-x không chạy với qca-ssdk hiện tại (xem mô tả bản vá 940, thread VOZ trang 2).
- Hiệu chuẩn 5 GHz (QCN6122) ở offset **`0x26800`** trong `0:ART` (không phải `0x4C000` của bản michioxd).
- Board name có thể là `fpt,wf810df` hoặc `fpt,ax3000cv2` — mọi khối `case` phải có cả hai.
- `qualcommax/patches-6.12/0199-...keep-the-CMN-block-bus-clocks-enabled`: chống treo/boot-loop IPQ5018 khi driver CMN PLL tắt clock bus sau probe (Stanislaw Pal, đã gửi upstream; ImmortalWrt 25.12 chỉ có cho kernel 6.18). **Giữ lại** cho tới khi ImmortalWrt tự có bản vá này cho 6.12 — khi đó xoá bản của mình để tránh trùng.
- `board-2.bin` (IPQ5018 và QCN6122) phải có thêm bản ghi **`qmi-board-id=255`** (cùng dữ liệu với 35 / 96). ImmortalWrt không có bản vá ath11k `210-...reading-board-id-from-devicetree` của zcop nên firmware báo board-id 255; thiếu bản ghi này thì cả hai radio không lên (đã thấy trên máy thật với bản b2, 08/10/2026). Bước 10 của workflow kiểm tra điều này.
- Giữ **BDF của zcop** trong `board-2.bin` (byte định danh 0x44/0x6e), không thay bằng BDF gốc FPT của michioxd (0x60/0x7d, `variant=FPT-AX3000CV2`): đã thử cả hai trên máy thật ngày 08/10/2026, chủ repo chọn zcop. Caldata vẫn lấy từ `0:ART` của máy (đã đối chiếu header khớp FPT).
- **Tailscale nằm sẵn trong firmware** (`kmod-tun`, `tailscale`, `luci-app-tailscale-community` trong `config/wf810df.seed`): kernel tự build nên `kmod-tun` từ kho chính hãng không khớp, `apk add tailscale` trên máy bị lỗi (08/10/2026). Bước 10 kiểm tra 3 gói này. Gói nào khác cũng cần kmod thì làm tương tự: đưa vào seed, không cài từ kho.
- Packet steering bật sẵn (`files/etc/uci-defaults/99-wf810df-vn`) vì IPQ5018 chỉ có 1 hàng đợi RX.
- NAND GD5F2GM7RE: 2 Gbit = 256 MB, trang 2048, khối 128 KB — khớp `PAGESIZE`/`BLOCKSIZE`.
- Không thêm biến thể `ath11k-smallbuffers`: PR OpenWrt #21495 chưa merge, còn lỗi Kconfig, và máy có 512 MB RAM nên không cần.

## Quy tắc quan trọng
- Bước 10 của workflow là kiểm tra an toàn (đủ 3 file ảnh, DTB đúng máy, kernel có YT921x, đủ driver Wi-Fi và `kmod-dsa-yt921x`, không có `default-settings-chn`). **Không được nới lỏng hay xoá để build qua.**
- Không đổi layout NAND (`rootfs` tại `0xd00000`, dài `0xf300000`), tên phân vùng `0:ART`, `0:APPSBLENV`, hay `DEVICE_DTS_CONFIG` khi chưa có bằng chứng từ máy thật.
- Không thêm `default-settings-chn`.
- Không push thẳng vào nhánh chính, không tự merge PR.

## Khi sửa lỗi build
- Lỗi mạng/mirror/timeout/hết dung lượng runner → báo cáo, đề nghị chạy lại, không sửa code.
- Bản vá kernel không áp được khi lên phiên bản ImmortalWrt mới → kiểm tra trước xem ImmortalWrt đã tự có driver YT921x chưa (khi đó bỏ bản vá trùng); nếu chưa thì chỉ sửa phần xung đột tối thiểu, ghi rõ trong PR.
- Gói bổ sung không tồn tại → báo tên gói, không tự thay bằng gói khác.

## Ngôn ngữ
- Trả lời, mô tả Issue/PR bằng tiếng Việt.
