import os
import subprocess
import cv2

# ================= CẤU HÌNH =================
LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9"
# Thay tên thiết bị của bạn vào đây (chọn 1 cái đang bật để chụp mẫu)
DEVICE_ID = "emulator-5556"
# ============================================

ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")

def adb_command(cmd):
    full_cmd = f'"{ADB_PATH}" -s {DEVICE_ID} {cmd}'
    subprocess.call(full_cmd, shell=True)

def capture_screen():
    print(f"Đang chụp màn hình thiết bị {DEVICE_ID}...")
    filename = "anh_goc_full.png"
    
    # Xóa file cũ nếu có
    if os.path.exists(filename):
        os.remove(filename)

    # Chụp và kéo về máy tính
    adb_command(f"shell screencap -p /sdcard/{filename}")
    adb_command(f"pull /sdcard/{filename} {filename}")
    
    if os.path.exists(filename):
        print(f"✅ Đã lưu ảnh thành công: {filename}")
        print("Bạn hãy mở file này bằng Paint để cắt nút nhé!")
        # Tự động mở ảnh lên cho bạn luôn
        os.startfile(filename)
    else:
        print("❌ Lỗi: Không chụp được ảnh. Kiểm tra lại tên thiết bị.")

if __name__ == "__main__":
    capture_screen()