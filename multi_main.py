import cv2
import numpy as np
import os
import time
import subprocess
import random
import threading

# ================= CẤU HÌNH =================
LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9" 
THRESHOLD = 0.85 

# Danh sách thiết bị (Cập nhật từ danh sách bạn gửi)
LIST_DEVICES = [
    "emulator-5554",
    "emulator-5556",
    "emulator-5558",
    "emulator-5562",
    "emulator-5564"
    # Nếu có thêm tab nữa (ví dụ emulator-5566), hãy thêm dòng này vào:
    # , "emulator-5566" 
]

# Danh sách nút thoát
LIST_NUT_THOAT = ["nut_thoat_1.png", "nut_thoat_2.png"]
# ============================================

ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")

def adb_command(device_id, cmd):
    """Gửi lệnh đến đúng thiết bị (device_id)"""
    # Thêm tham số -s {device_id} để chỉ định giả lập cụ thể
    full_cmd = f'"{ADB_PATH}" -s {device_id} {cmd}'
    subprocess.call(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def tap(device_id, x, y):
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    # Tắt print tọa độ để đỡ rối mắt khi chạy nhiều tab
    # print(f"[{device_id}] Click {rand_x}, {rand_y}") 
    adb_command(device_id, f"shell input tap {rand_x} {rand_y}")

def capture_screen(device_id):
    """Mỗi device lưu 1 file ảnh riêng biệt"""
    # Tạo tên file ảnh riêng: screen_emulator-5554.png
    filename = f"screen_{device_id}.png"
    
    adb_command(device_id, f"shell screencap -p /sdcard/{filename}")
    adb_command(device_id, f"pull /sdcard/{filename} {filename}")
    return cv2.imread(filename), filename

def find_image(template_name, screen_img):
    if screen_img is None: return None
    if not os.path.exists(template_name): return None  
    template = cv2.imread(template_name)
    res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    if max_val >= THRESHOLD:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y)
    return None

def run_bot(device_id):
    """Hàm chạy độc lập cho từng giả lập (Luồng riêng)"""
    print(f"--- Đã khởi động Bot cho: {device_id} ---")
    
    # Kết nối lại 1 lần cho chắc
    # (Với tên emulator-xxxx thì thường không cần connect IP, nhưng cứ để lệnh trống để ADB refresh)
    
    last_check_time = 0 
    
    # Random thời gian khởi động để các tab không click cùng lúc (tránh lag)
    time.sleep(random.uniform(0, 10)) 

    while True:
        try:
            # Chụp màn hình (Lưu vào file riêng)
            screen, filename = capture_screen(device_id)
            
            if screen is None:
                time.sleep(1)
                continue

            # ================= LOGIC AUTO =================

            # 1. XỬ LÝ LỖI TREO MÁY
            wait_pos = find_image("nut_doi.png", screen)
            if wait_pos:
                print(f"[{device_id}] LỖI -> Bấm Đợi")
                tap(device_id, *wait_pos)
                time.sleep(1)
                continue 

            # 2. QUÉT NÚT THOÁT (Ưu tiên)
            found_exit = False
            for exit_img in LIST_NUT_THOAT:
                exit_pos = find_image(exit_img, screen)
                if exit_pos:
                    print(f"[{device_id}] GAME -> Bấm Thoát ({exit_img})")
                    tap(device_id, *exit_pos)
                    time.sleep(8)
                    found_exit = True
                    break
            if found_exit: continue

            # 3. ĐẦU HÀNG (Nếu nút sáng)
            sur_pos = find_image("surrender_btn.png", screen)
            if sur_pos:
                print(f"[{device_id}] ĐẦU HÀNG -> Bấm ngay!")
                tap(device_id, *sur_pos)
                time.sleep(1)
                
                # Xác nhận (Phải chụp lại màn hình mới)
                screen_conf, _ = capture_screen(device_id)
                conf_pos = find_image("confirm_surrender.png", screen_conf)
                if conf_pos: 
                    tap(device_id, *conf_pos)
                    print(f"[{device_id}] Đã xác nhận. Đợi...")
                    time.sleep(10)
                continue

            # 4. SẢNH CHỜ
            pos_accept = find_image("accept.png", screen)
            if pos_accept:
                print(f"[{device_id}] SẢNH -> Chấp nhận")
                tap(device_id, *pos_accept)
                last_check_time = time.time() 
                time.sleep(3) 
                continue

            pos_find = find_image("find_match.png", screen)
            if pos_find:
                print(f"[{device_id}] SẢNH -> Tìm trận")
                tap(device_id, *pos_find)
                time.sleep(3)
                continue

            # 5. CHECK MENU ĐỊNH KỲ (Mỗi 20s + Random 5s)
            current_time = time.time()
            if current_time - last_check_time > 20 + random.randint(0, 5): 
                print(f"[{device_id}] CHECK -> Mở menu")
                
                gear_pos = find_image("settings_icon.png", screen)
                if not gear_pos:
                    expand_pos = find_image("nut_mo_rong.png", screen)
                    if expand_pos:
                        tap(device_id, *expand_pos)
                        time.sleep(1) 
                else:
                    tap(device_id, *gear_pos)

                last_check_time = time.time()

            # Xóa file ảnh tạm để đỡ rác ổ cứng
            try: os.remove(filename) 
            except: pass

            time.sleep(1) 

        except Exception as e:
            print(f"[{device_id}] Lỗi: {e}")
            time.sleep(5)

def main():
    print(f"=== KHỞI ĐỘNG MULTI-THREAD CHO {len(LIST_DEVICES)} THIẾT BỊ ===")
    
    threads = []
    
    # Tạo luồng cho từng thiết bị
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot, args=(dev,))
        t.daemon = True # Để khi tắt CMD thì luồng cũng tắt theo
        threads.append(t)
        t.start()
        print(f"-> Đã tạo luồng xử lý cho {dev}")
        time.sleep(2) # Khởi động lần lượt cách nhau 2s để CPU không bị sốc
        
    # Giữ chương trình chính chạy để các luồng con hoạt động
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Đang dừng toàn bộ...")

if __name__ == "__main__":
    main()