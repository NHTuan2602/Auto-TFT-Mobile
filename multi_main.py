import cv2
import numpy as np
import os
import time
import subprocess
import random
import threading
import json

# ================= 1. CẤU HÌNH TỰ ĐỘNG =================
def load_config():
    config_file = "config.json"
    default_config = {
        "LDPLAYER_PATH": r"C:\LDPlayer\LDPlayer9",
        "THRESHOLD": 0.85,
        "LIST_DEVICES": ["emulator-5554", "emulator-5556"], 
        "GHI_CHU": "Điền tên thiết bị vào đây (ngăn cách bằng dấu phẩy)."
    }
    if not os.path.exists(config_file):
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        except: pass
        return default_config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return default_config

config_data = load_config()
LDPLAYER_PATH = config_data.get("LDPLAYER_PATH", r"C:\LDPlayer\LDPlayer9")
ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")
THRESHOLD = config_data.get("THRESHOLD", 0.85)
LIST_DEVICES = config_data.get("LIST_DEVICES", [])

# ================= 2. DANH SÁCH ẢNH MẪU =================
LIST_NUT_THOAT = ["nut_thoat_1.png", "nut_thoat_2.png", "nut_thoat_3.png"]
LIST_POPUP = ["nut_dong_popup.png", "nut_dong_popup_1.png", "nut_dong_popup_2.png"] 
LIST_NUT_VAO_TRAN = ["find_match.png", "nut_choi_main.png"]

# ================= 3. CÁC HÀM HỖ TRỢ =================
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
            if img is not None: return img, filename
        except: pass
    return None, filename

def find_image(template_name, screen_img):
    if screen_img is None: return None
    if not os.path.exists(template_name): return None  
    template = cv2.imread(template_name)
    if template is None: return None
    try:
        res = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val >= THRESHOLD:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)
    except: pass
    return None

def force_stop_game(device_id):
    """Hàm tắt hẳn ứng dụng (Kill App)"""
    print(f"[{device_id}] ⚠️ FORCE STOP: Đang tắt game để khởi động lại...")
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttacticsvn") # Bản VNG
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttactics")   # Bản Quốc tế
    time.sleep(2)
    adb_command(device_id, "shell input keyevent 3") # Về Home

# ================= 4. LOGIC AUTO CHÍNH =================
def run_bot(device_id):
    print(f"--- Đã khởi động Bot: {device_id} ---")
    
    last_check_time = 0 
    lobby_stuck_start = 0 
    popup_spam_count = 0 
    mode_spam_count = 0 
    
    time.sleep(random.uniform(0, 5)) 

    while True:
        try:
            screen, filename = capture_screen(device_id)
            if screen is None:
                time.sleep(0.5)
                continue

            # --- A. ƯU TIÊN CAO NHẤT: XỬ LÝ LỖI & KHỞI ĐỘNG ---
            
            # 1. Phát hiện lỗi kết nối -> Kill App ngay
            if find_image("loi_ket_noi.png", screen):
                print(f"[{device_id}] ❌ LỖI KẾT NỐI -> Kill App!")
                force_stop_game(device_id)
                time.sleep(5) 
                continue

            # 2. Mở lại game (SỬA LẠI THỜI GIAN CHỜ)
            if find_image("icon_game.png", screen):
                print(f"[{device_id}] ♻️ Thấy Icon Game -> Mở lại.")
                tap(device_id, *find_image("icon_game.png", screen))
                
                # [SỬA ĐỔI QUAN TRỌNG]
                # Thay vì ngủ 40s, chỉ ngủ 5s.
                # Sau 5s, vòng lặp tiếp theo sẽ chạy:
                # - Nếu có bảng OpenGL -> Nó sẽ xuống mục số 4 bên dưới để bấm OK ngay.
                # - Nếu có bảng Update -> Nó bấm Update.
                # - Nếu game đang tải -> Nó không làm gì, cứ quét tiếp.
                print(f"[{device_id}] Đã bấm mở game. Đợi 5s để check OpenGL...")
                time.sleep(5) 
                continue

            # 3. Tắt Popup (Quảng cáo, Mời chơi)
            found_popup = False
            for popup_img in LIST_POPUP:
                popup_pos = find_image(popup_img, screen)
                if popup_pos:
                    if popup_spam_count < 3: 
                        print(f"[{device_id}] Tắt Popup: {popup_img}")
                        tap(device_id, *popup_pos)
                        time.sleep(0.5)
                        popup_spam_count += 1
                        found_popup = True
                        break
            if not found_popup: popup_spam_count = 0
            if found_popup and popup_spam_count < 3: continue

            # 4. Xử lý OpenGL & Update (Sẽ được xử lý ngay sau khi mở game 5s)
            if find_image("nut_ok_opengl.png", screen):
                print(f"[{device_id}] ⚠️ Thấy bảng OpenGL -> Bấm OK ngay!")
                tap(device_id, *find_image("nut_ok_opengl.png", screen))
                time.sleep(2) # Bấm xong đợi xíu cho nó tải tiếp
                continue
                
            if find_image("nut_cap_nhat.png", screen):
                print(f"[{device_id}] Thấy nút Cập nhật -> Bấm luôn.")
                tap(device_id, *find_image("nut_cap_nhat.png", screen))
                time.sleep(10) # Bấm cập nhật xong đợi 10s check lại
                continue
                
            if find_image("nut_mo_game.png", screen):
                tap(device_id, *find_image("nut_mo_game.png", screen))
                time.sleep(10)
                continue

            # --- B. XỬ LÝ SẢNH (SPEED MODE) ---
            pos_play_active = None
            for btn_play in LIST_NUT_VAO_TRAN:
                pos_play_active = find_image(btn_play, screen)
                if pos_play_active: break 
            
            if not pos_play_active:
                if mode_spam_count < 2: 
                    pos_new = find_image("nut_che_do_moi.png", screen)
                    if pos_new:
                        print(f"[{device_id}] Chọn Chế độ MỚI")
                        tap(device_id, *pos_new)
                        mode_spam_count += 1
                        time.sleep(0.5)
                        continue

                    pos_normal = find_image("nut_che_do_thuong.png", screen)
                    if pos_normal:
                        print(f"[{device_id}] Chọn Chế độ THƯỜNG")
                        tap(device_id, *pos_normal)
                        mode_spam_count += 1
                        time.sleep(0.5)
                        continue
            
            if pos_play_active:
                print(f"[{device_id}] => Bấm CHƠI / TÌM TRẬN")
                tap(device_id, *pos_play_active)
                time.sleep(3) 
                
                if lobby_stuck_start == 0: lobby_stuck_start = time.time()
                elif time.time() - lobby_stuck_start > 60:
                    print(f"[{device_id}] Lỗi treo sảnh -> Bấm Quay lại")
                    if find_image("nut_quay_lai.png", screen):
                        tap(device_id, *find_image("nut_quay_lai.png", screen))
                    else:
                        tap(device_id, *pos_play_active)
                    lobby_stuck_start = 0
                    mode_spam_count = 0
                continue
            else:
                lobby_stuck_start = 0
                if mode_spam_count >= 2: mode_spam_count = 0

            # --- C. TRONG GAME ---
            if find_image("accept.png", screen):
                tap(device_id, *find_image("accept.png", screen))
                time.sleep(1) 
                continue

            if find_image("nut_doi.png", screen):
                tap(device_id, *find_image("nut_doi.png", screen))
                time.sleep(0.5)
                continue

            found_exit = False
            for exit_img in LIST_NUT_THOAT:
                pos = find_image(exit_img, screen)
                if pos:
                    print(f"[{device_id}] Thoát trận")
                    tap(device_id, *pos)
                    time.sleep(5)
                    found_exit = True
                    break
            if found_exit: continue

            if find_image("surrender_btn.png", screen):
                tap(device_id, *find_image("surrender_btn.png", screen))
                time.sleep(0.5)
                screen_conf, _ = capture_screen(device_id)
                if find_image("confirm_surrender.png", screen_conf):
                    tap(device_id, *find_image("confirm_surrender.png", screen_conf))
                    time.sleep(8)
                continue

            # --- D. MENU CHECK ---
            current_time = time.time()
            if current_time - last_check_time > 20 + random.randint(0, 5): 
                if not find_image("settings_icon.png", screen):
                    if find_image("nut_mo_rong.png", screen):
                        tap(device_id, *find_image("nut_mo_rong.png", screen))
                        time.sleep(0.5)
                else:
                    tap(device_id, *find_image("settings_icon.png", screen))
                last_check_time = time.time()

            try: os.remove(filename) 
            except: pass
            time.sleep(1)

        except Exception as e:
            print(f"[{device_id}] Lỗi: {e}")
            time.sleep(3)

def main():
    print(f"=== BOT AUTO TFT - FINAL (SMART START) ===")
    if not LIST_DEVICES:
        print("❌ LỖI: Danh sách thiết bị trống!")
        return
    threads = []
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot, args=(dev,))
        t.daemon = True 
        threads.append(t)
        t.start()
        print(f"-> Đã khởi tạo luồng cho thiết bị: {dev}")
        time.sleep(1) 
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Đang dừng...")

if __name__ == "__main__":
    main()