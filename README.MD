
```markdown
<div align="center">

# 🏆 Auto TFT Mobile - Tool Cày Pass Tự Động
### Automation Bot for Teamfight Tactics Mobile (LDPlayer)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-win?style=flat&logo=windows)
![Emulator](https://img.shields.io/badge/Emulator-LDPlayer_9-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

<br>

**Phiên bản tối ưu hóa tốc độ, đa luồng và khả năng tự phục hồi lỗi.**
*Sử dụng công nghệ xử lý ảnh (OpenCV) và ADB để tự động hóa thao tác.*

[Tải Xuống Ngay (Latest Release)](https://github.com/NHTuan2602/Auto-TFT-Mobile-VNG/releases/tag/AutoTFTMobile) • [Báo Lỗi](https://github.com/NHTuan2602/Auto-TFT-Mobile-VNG/issues)

</div>

---

## 🚀 Tính Năng Nổi Bật

| Tính năng | Mô tả chi tiết |
| :--- | :--- |
| **🔄 Smart Recovery** | Tự động phát hiện lỗi "Mất kết nối", "Lỗi đăng nhập" để buộc dừng (Force Stop) và mở lại game từ đầu. |
| **⚡ Speed Mode** | Tối ưu hóa vòng lặp, giảm độ trễ, bot phản xạ chọn trận và chấp nhận trận đấu ngay lập tức. |
| **🛠️ Auto Fix** | Tự động phát hiện và xử lý các thông báo **OpenGL** hoặc **Cập nhật** chỉ sau 5 giây (thay vì chờ 40s như bản cũ). |
| **🎮 Chế độ Thông minh** | Ưu tiên chọn **Chế độ Mới** (Sự kiện). Nếu không có sẽ tự động chuyển sang **Chế độ Thường**. |
| **💻 Đa Luồng (Multi)** | Hỗ trợ chạy song song nhiều thiết bị giả lập cùng lúc, không chiếm chuột máy tính. |
| **🚫 Anti-Stuck** | Tự động thoát menu, tắt quảng cáo/thông báo rác, tự động reset sảnh nếu bị kẹt. |

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### 1. Cấu hình Giả lập (BẮT BUỘC)
Để Bot hoạt động chính xác 100%, bạn cần thiết lập **LDPlayer 9** đúng theo bảng dưới đây:

| Mục | Cài đặt Yêu cầu | Lý do |
| :--- | :--- | :--- |
| **Độ phân giải** | **1280x720 (dpi 240)** | Khớp với tọa độ ảnh mẫu nhận diện của Bot. |
| **ADB Debugging** | **Open Connection (Bật)** | Cấp quyền cho Tool gửi lệnh điều khiển. |
| **CPU / RAM** | 2 Cores / 2GB RAM | Cấu hình tối ưu để treo nhiều tab nhẹ máy. |
| **Root** | Tắt (Disable) | Tránh các lỗi bảo mật hoặc crash game. |
| **Ingame** | **Linh thú mặc định (Thủy Thần)** | Để bot nhận diện thanh máu chính xác nhất. |

<div align="center">
  <img src="images/setting.png" width="600" alt="Cài đặt LDPlayer">
</div>

### 2. Cấu trúc thư mục chuẩn
Sau khi tải về và giải nén, thư mục Tool của bạn phải đầy đủ các file như sau mới chạy được:

```text
AutoTFT_Final/
├── multi_main.exe          # File chạy chính
├── config.json             # File cấu hình (Tự tạo sau lần chạy đầu)
├── adb.exe                 # Bộ kết nối ADB (Bắt buộc)
├── AdbWinApi.dll           # Thư viện ADB
├── AdbWinUsbApi.dll        # Thư viện ADB
├── images/                 # (Tùy chọn) Thư mục chứa ảnh hướng dẫn
│
├── [Nhóm Ảnh Hệ Thống]     # icon_game, loi_ket_noi, nut_cap_nhat...
├── [Nhóm Ảnh Sảnh]         # find_match, nut_che_do_moi, nut_quay_lai...
└── [Nhóm Ảnh Trong Game]   # accept, surrender_btn, confirm_surrender...

```

---

## 📝 Hướng Dẫn Sử Dụng

### Bước 1: Lấy ID thiết bị (Tùy chọn)

Mở CMD và gõ lệnh `adb devices` để xem danh sách các giả lập đang bật.

<div align="center">
<img src="images/adb.png" width="500" alt="ADB Devices">
</div>

### Bước 2: Chạy Tool & Cấu hình

1. Mở file `multi_main.exe` (Chạy dưới quyền **Administrator** để ổn định nhất).
2. Giao diện Tool hiện lên, bạn nhập:
* **Đường dẫn LDPlayer:** (Ví dụ: `C:\LDPlayer\LDPlayer9`)
* **Danh sách thiết bị:** Nhập tên (vd: `emulator-5554`) hoặc copy từ bảng `adb devices` vào.


3. Bấm **BẮT ĐẦU**.

<div align="center">
<img src="images/app.png" width="500" alt="Giao diện App">





<i>Giao diện cấu hình trực quan, hỗ trợ Log chi tiết</i>
</div>

---

## 📅 Changelog (Lịch sử cập nhật)

<details open>
<summary><b>🔥 [24/01/2026] - Bản cập nhật "Auto Restart & Smart Wait"</b></summary>




* **Tính năng mới:** Thêm hàm `force_stop_game` để tắt hẳn ứng dụng khi gặp lỗi kết nối (khắc phục lỗi kẹt nút "Thử lại").
* **Tối ưu:** Sửa logic khởi động game (Bấm icon -> Chờ 5s -> Check lỗi ngay).
* **Sửa lỗi:** Cập nhật tên gói (Package Name) chính xác cho bản VNG và Riot Quốc tế.

</details>

<details>
<summary><b>⚡ [23/01/2026] - Bản cập nhật Speed & Logic</b></summary>




* **Tối ưu:** Giảm độ trễ vòng lặp xuống 1s để tăng tốc độ phản xạ.
* **Sửa lỗi:** Fix lỗi vòng lặp vô tận khi chọn chế độ.
* **Tính năng:** Tự động reset sảnh (nút Back) nếu kẹt nút tìm trận quá 60s.

</details>

---

## ⚠️ Tuyên bố miễn trừ trách nhiệm (Disclaimer)

> [!WARNING]
> Công cụ này được phát triển với mục đích **học tập, nghiên cứu lập trình Python** và tự động hóa (Automation).

1. Việc sử dụng phần mềm thứ 3 có thể vi phạm điều khoản dịch vụ của Nhà phát hành game.
2. Tác giả **không chịu trách nhiệm** về bất kỳ rủi ro nào đối với tài khoản của bạn (khóa nick, mất vật phẩm...).
3. Nếu gặp lỗi **"ADB Offline"**: Hãy thử Tắt/Bật lại chế độ ADB Debugging trong cài đặt LDPlayer hoặc khởi động lại giả lập.

<div align="center">
<img src="images/local.png" width="500" alt="Fix ADB Offline">
</div>

---

<div align="center">
<i>Made with ❤️ by [NHTuan2602]</i>
</div>

