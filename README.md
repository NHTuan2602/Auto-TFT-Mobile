# Auto TFT Mobile - Bot Cày Token/Exp Tự Động (ADB Version)

Tool tự động hóa chơi Đấu Trường Chân Lý (TFT) Mobile trên giả lập LDPlayer sử dụng Python, ADB và nhận diện hình ảnh (OpenCV). Hỗ trợ chạy nhiều tài khoản cùng lúc (Multi-thread).

## 🚀 Tính Năng Chính
- **Tự động Tìm trận & Chấp nhận trận đấu.**
- **Tự động Đầu hàng (Surrender):** Tự động bấm đầu hàng ngay khi nút sáng màu (check liên tục).
- **Tự động Thoát trận:** Nhận diện khi bị loại hoặc kết thúc trận để thoát về sảnh nhanh chóng.
- **Xử lý Menu thông minh:** Tự động tìm nút mở rộng hoặc bánh răng cài đặt.
- **Chống treo:** Tự động xử lý lỗi "System UI không phản hồi" (nút Đợi).
- **Hỗ trợ Đa luồng (Multi-threading):** Chạy ổn định 5-6 giả lập cùng lúc trên một máy tính.

---

## 🛠️ Yêu Cầu Cài Đặt

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:

1.  **[LDPlayer 9](https://vn.ldplayer.net/):** Giả lập Android ổn định nhất.
2.  **[Python 3.10+](https://www.python.org/downloads/):** (Nhớ tích chọn "Add Python to PATH" khi cài).
3.  **Thư viện Python:** Chạy lệnh sau trong CMD để cài đặt:
    ```bash
    pip install opencv-python numpy
    ```

---

## ⚙️ Cấu Hình LDPlayer (BẮT BUỘC)

Để tool hoạt động chính xác 100%, bạn phải thiết lập LDPlayer **giống hệt** các thông số dưới đây. Nếu sai độ phân giải, tool sẽ không click được.

### 1. Cài đặt Nâng cao (Advanced)
Vào **Cài đặt (Settings)** -> Tab **Nâng cao (Advanced)**:

* **Độ phân giải (Resolution):** Chọn **Máy tính bảng (Tablet)** -> **1280x720 (dpi 240)**.
* **CPU:** Chọn **4 cores** (để giả lập mượt, không bị crash).
* **RAM:** Chọn **4096M (4GB)** (tránh lỗi tràn RAM khi chạy lâu).
* **Ổ dùng chung:** Chọn "System.vmdk chia sẻ và chỉ đọc".

> *Lưu ý: Sau khi chỉnh xong, bấm **Lưu** và khởi động lại giả lập.*

### 2. Bật kết nối ADB (Tab Khác)
Vào tab **Khác (Other settings)**:
* Tìm dòng **ADB Debugging** (Gỡ lỗi ADB).
* Chuyển thành: **Open Connection (Bật kết nối)**.
* Bấm **Lưu** và Khởi động lại giả lập lần nữa.

### 3. Cài đặt trong Game TFT
* **Ngôn ngữ:** Tiếng Việt.
* **Đồ họa:** Chỉnh xuống mức **THẤP NHẤT** (để chạy nhẹ máy).
* **FPS:** Khóa ở 30 hoặc 60 FPS.

---

## 📝 Hướng Dẫn Sử Dụng

### Bước 1: Lấy danh sách thiết bị
Nếu bạn chạy nhiều tab giả lập, hãy mở hết chúng lên, sau đó vào CMD gõ:
```bash
adb devices
Bước 2: Cập nhật Code
Mở file multi_main.py và cập nhật danh sách thiết bị của bạn vào biến LIST_DEVICES:

Python

LIST_DEVICES = [
    "emulator-5554",
    "emulator-5556",
    "emulator-5558",
    "emulator-5562",
    "emulator-5564"
]
Bước 3: Chạy Tool
Mở CMD tại thư mục chứa code và gõ lệnh:

Bash

python multi_main.py
⚠️ Khắc Phục Lỗi Thường Gặp
1. Tool báo lỗi "Thiếu file ảnh" hoặc không click:

Nguyên nhân: Do độ phân giải màn hình của bạn khác với ảnh mẫu, hoặc tên file ảnh bị sai.

Khắc phục: Xóa các file ảnh mẫu cũ (.png). Chạy tool 1 lần để nó tự chụp màn hình (screen_xxxx.png). Mở ảnh đó lên bằng Paint và cắt lại các nút bấm (Tìm trận, Chấp nhận, Đầu hàng...) rồi lưu đè vào thư mục.

2. Lỗi ADB Offline:

Khắc phục: Vào cài đặt LDPlayer -> Tắt "ADB Debugging" đi rồi Bật lại -> Lưu.

3. Tool chạy nhưng không thấy click:

Kiểm tra xem bạn đã để file ảnh mẫu (.png) chung thư mục với file multi_main.py chưa. Không được để ảnh trong thư mục con.sss