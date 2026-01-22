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

# Danh sách thiết bị
LIST_DEVICES = [
    "emulator-5554",
    "emulator-5556",
    "emulator-5558",
    "emulator-5560",
    "emulator-5562",
    "emulator-5564"
]

LIST_NUT_THOAT = ["nut_thoat_1.png", "nut_thoat_2.png"]
# ============================================

ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")

def adb_command(device_id, cmd):
    full_cmd = f'"{ADB_PATH}" -s {device_id} {cmd}'
    subprocess.call(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def tap(device_id, x, y):
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    full_cmd = f'"{ADB_PATH}" -s {device_id} shell input tap {rand_x} {rand_y}'
    subprocess.call(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def capture_screen(device_id):
    filename = f"screen_{device_id}.png"
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass

    adb_command(device_id, f"shell screencap -p /sdcard/{filename}")
    adb_command(device_id, f"pull /sdcard/{filename} {filename}")
    
    if os.path.exists(filename):
        try:
            img = cv2.imread(filename)
            if img is not None:
                return img, filename
        except: pass
    return None, filename

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
    print(f"--- Đã khởi động Bot cho: {device_id} ---")
    last_check_time = 0 
    time.sleep(random.uniform(0, 10)) 

    while True:
        try:
            screen, filename = capture_screen(device_id)
            if screen is None:
                time.sleep(1)
                continue

            # ================= LOGIC AUTO =================

            # 1. MÀN HÌNH CHỜ & CẬP NHẬT (Ưu tiên cao nhất)
            
            # Nếu thấy nút "CHƠI" to đùng ở Main Menu -> Bấm vào
            pos_main_play = find_image("nut_choi_main.png", screen)
            if pos_main_play:
                print(f"[{device_id}] MAIN -> Thấy nút CHƠI, vào sảnh ngay.")
                tap(device_id, *pos_main_play)
                time.sleep(5) # Chờ load vào sảnh
                continue

            # Nếu thấy nút "Thường" (Trong bảng chọn chế độ) -> Chọn nó
            pos_normal = find_image("nut_che_do_thuong.png", screen)
            if pos_normal:
                print(f"[{device_id}] SẢNH -> Chọn chế độ Thường")
                tap(device_id, *pos_normal)
                time.sleep(1)
                continue

            # Các logic Update/OpenGL cũ
            opengl_pos = find_image("nut_ok_opengl.png", screen)
            if opengl_pos:
                tap(device_id, *opengl_pos)
                time.sleep(2)
                continue

            update_pos = find_image("nut_cap_nhat.png", screen)
            if update_pos:
                print(f"[{device_id}] UPDATE -> Bấm Cập nhật.")
                tap(device_id, *update_pos)
                print(f"[{device_id}] Đang tải... Ngủ 60s...")
                time.sleep(60) 
                continue

            play_pos = find_image("nut_mo_game.png", screen) 
            if play_pos:
                print(f"[{device_id}] UPDATE XONG -> Vào lại game.")
                tap(device_id, *play_pos)
                time.sleep(20) 
                continue

            # 2. XỬ LÝ LỖI TREO
            wait_pos = find_image("nut_doi.png", screen)
            if wait_pos:
                tap(device_id, *wait_pos)
                time.sleep(1)
                continue 

            # 3. TRONG GAME (Thoát & Đầu hàng)
            found_exit = False
            for exit_img in LIST_NUT_THOAT:
                exit_pos = find_image(exit_img, screen)
                if exit_pos:
                    print(f"[{device_id}] GAME -> Bấm Thoát")
                    tap(device_id, *exit_pos)
                    time.sleep(8)
                    found_exit = True
                    break
            if found_exit: continue

            sur_pos = find_image("surrender_btn.png", screen)
            if sur_pos:
                print(f"[{device_id}] ĐẦU HÀNG -> Bấm ngay!")
                tap(device_id, *sur_pos)
                time.sleep(1)
                
                screen_conf, _ = capture_screen(device_id)
                conf_pos = find_image("confirm_surrender.png", screen_conf)
                if conf_pos: 
                    tap(device_id, *conf_pos)
                    print(f"[{device_id}] Đã xác nhận. Đợi...")
                    time.sleep(10)
                continue

            # 4. SẢNH CHỜ (Tìm trận)
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

            # 5. MENU CHECK (Chống kẹt)
            current_time = time.time()
            if current_time - last_check_time > 20 + random.randint(0, 5): 
                # print(f"[{device_id}] CHECK -> Mở menu")
                gear_pos = find_image("settings_icon.png", screen)
                if not gear_pos:
                    expand_pos = find_image("nut_mo_rong.png", screen)
                    if expand_pos:
                        tap(device_id, *expand_pos)
                        time.sleep(1) 
                else:
                    tap(device_id, *gear_pos)
                last_check_time = time.time()

            try: os.remove(filename) 
            except: pass
            time.sleep(1) 

        except Exception as e:
            print(f"[{device_id}] Lỗi: {e}")
            time.sleep(5)

def main():
    print(f"=== KHỞI ĐỘNG BOT (6 TAB) ===")
    threads = []
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot, args=(dev,))
        t.daemon = True 
        threads.append(t)
        t.start()
        print(f"-> Đã tạo luồng cho {dev}")
        time.sleep(2) 
        
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Đang dừng...")

if __name__ == "__main__":
    main()