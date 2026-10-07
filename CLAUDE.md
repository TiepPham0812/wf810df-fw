# Quy tắc dự án wf810df-fw

## Mục tiêu
- Firmware **ImmortalWrt biên dịch từ mã nguồn chính hãng** cho **FPT AX3000CV2** (Actiontec/CIG WF-810DF, Qualcomm IPQ5018, NAND 256 MB, RAM 512 MB).
- Phần hỗ trợ thiết bị lấy từ `michioxd/openwrt-wf810df` (OpenWrt 25.12), không fork nguyên cây nguồn.
- Thiết bị còn thử nghiệm: **3 cổng LAN (switch YT9215S qua MDIO bit-bang) chưa lên link, NSS chưa chạy.** WAN, Wi-Fi 2.4/5 GHz, NAND, nút bấm chạy.

## Cấu trúc
- `device/` — file chép thẳng vào cây nguồn: DTS `ipq5018-ax3000cv2.dts`, 2 bản vá kernel driver YT921x (`9990-*`, `9991-*`).
- `scripts/add-device.py` — chèn thiết bị vào các file chung của ipq50xx (image, 02_network, caldata Wi-Fi, platform.sh, uboot-env, config kernel). Chỉ chèn thêm, không ghi đè; không tìm thấy mốc thì dừng.
- `files/` — chép vào firmware: `board-2.bin` Wi-Fi (IPQ5018 + QCN6122, dump từ máy gốc), múi giờ VN.
- `config/wf810df.seed` — cấu hình gói.
- `.github/workflows/build-wf810df.yml` — tải ImmortalWrt theo tag, ghép thiết bị, build (2–4 giờ).

## Quy tắc quan trọng
- Tên bản vá kernel phải sắp xếp đúng thứ tự (`ls | sort`): bản backport driver (`9990`) **trước** bản cập nhật zcop (`9991`). Không đặt tên kiểu `10000-` (sẽ chạy trước `9999-`).
- Không dùng `ipq-wifi-fpt_ax3000cv2` (kho qca-wireless chính hãng không có board file máy này) — board data nằm ở `files/lib/firmware/ath11k/`.
- Bước 10 của workflow là kiểm tra an toàn (đủ 3 file ảnh, DTB đúng máy, kernel có YT921x, đủ driver Wi-Fi, không có `default-settings-chn`). **Không được nới lỏng hay xoá để build qua.**
- Không đổi layout UBI, offset NAND `0xd00000`, hay tên phân vùng `0:ART`, `0:APPSBLENV` khi chưa có bằng chứng từ máy thật.
- Không thêm `default-settings-chn`.
- Không push thẳng vào nhánh chính, không tự merge PR.

## Khi sửa lỗi build
- Lỗi mạng/mirror/timeout/hết dung lượng runner → báo cáo, đề nghị chạy lại, không sửa code.
- Bản vá kernel không áp được khi lên phiên bản ImmortalWrt mới → chỉ sửa phần xung đột tối thiểu, ghi rõ trong PR.
- Gói bổ sung không tồn tại → báo tên gói, không tự thay bằng gói khác.

## Ngôn ngữ
- Trả lời, mô tả Issue/PR bằng tiếng Việt.
