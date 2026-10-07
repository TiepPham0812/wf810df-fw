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
- `scripts/add-device.py` — thêm gói `kmod-dsa-yt921x`, khai báo image `wf810df`, chèn thiết bị vào 02_network, caldata, platform.sh, uboot-env. Chỉ chèn thêm; không tìm thấy mốc thì dừng.
- `files/` — chép vào firmware: `board-2.bin` Wi-Fi (từ zcop), múi giờ VN.
- `config/wf810df.seed` — cấu hình gói.
- `.github/workflows/build-wf810df.yml` — tải ImmortalWrt theo tag, ghép thiết bị, build (2–4 giờ).

## Những điểm đã có bằng chứng — KHÔNG đổi lại
- **Không reset cứng switch** và **không dùng `2500base-x`** cho cổng CPU: reset xoá thanh ghi U-Boot đã cấu hình → LAN mất link; 2500base-x không chạy với qca-ssdk hiện tại (xem mô tả bản vá 940, thread VOZ trang 2).
- Hiệu chuẩn 5 GHz (QCN6122) ở offset **`0x26800`** trong `0:ART` (không phải `0x4C000` của bản michioxd).
- Board name có thể là `fpt,wf810df` hoặc `fpt,ax3000cv2` — mọi khối `case` phải có cả hai.

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
