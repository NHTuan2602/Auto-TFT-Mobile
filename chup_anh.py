import cv2
import numpy as np
import os
import time
import subprocess
import random
import threading
import json
from datetime import datetime

# ================= 1. CẤU HÌNH HỆ THỐNG =================
def load_config():
    config_file = "config.json"
    default_config = {
        "LDPLAYER_PATH": r"C:\LDPlayer\LDPlayer9",
        "THRESHOLD": 0.85,
        "LIST_DEVICES": [
            "emulator-5554", "emulator-5556", "emulator-5558", 
            "emulator-5560", "emulator-5562", "emulator-5564"
        ], 
        "GHI_CHU": "Điền tên thiết bị vào đây."
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

# ================= 2. PHÂN LOẠI ẢNH MẪU (ĐÃ GỘP) =================

NUT_LOI_KET_NOI = "loi_ket_noi.png"
ICON_GAME = "icon_game.png"
NUT_CAP_NHAT = "nut_cap_nhat.png"
NUT_THOAT_CAP_NHAT = "nut_thoat_1.png" 

# [Ý TƯỞNG MỚI] Gộp chung OpenGL và Xác nhận đầu hàng vào 1 nhóm
# Bot thấy cái nào bấm cái đó, không quan tâm là OpenGL hay Đầu hàng
LIST_NUT_XAC_NHAN_CHUNG = [
    "nut_ok_opengl.png",       # Nút OK lỗi OpenGL
    "confirm_surrender.png"    # Nút Xác nhận đầu hàng
]

# Nhóm Thoát Trận (Exit Btn)
LIST_NUT_THOAT_THUA = ["nut_thoat_2.png", "nut_thoat_chung.png"] 

# Nhóm Chuỗi Kết Thúc
NUT_TIEP_TUC = "nut_thoat_3.png" 
NUT_CHOI_LAI = "nut_thoat_4.png" 

# Nhóm Popup & Cửa hàng
NUT_DONG_CUA_HANG = "nut_mo_rong.png" 
LIST_POPUP_RAC = [
    "nut_dong_popup.png", "nut_dong_popup_1.png",    
    "nut_dong_popup_2.png", "nut_dong_popup_3.png",
    "nut_dong_cua_hang.png"
] 

# Vào trận
LIST_NUT_VAO_TRAN = ["find_match.png", "nut_choi_main.png"]

# ================= 3. CÁC HÀM HỖ TRỢ =================
def log(device_id, msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{device_id}] ➤ {msg}")

def adb_command(device_id, cmd):
    full_cmd = f'"{ADB_PATH}" -s {device_id} {cmd}'
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except: pass

def tap(device_id, x, y):
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    full_cmd = f'"{ADB_PATH}" -s {device_id} shell input tap {rand_x} {rand_y}'
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except: pass

def capture_screen(device_id):
    filename = f"screen_{device_id}.png"
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass
    try:
        subprocess.run(f'"{ADB_PATH}" -s {device_id} shell screencap -p /sdcard/{filename}', 
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        subprocess.run(f'"{ADB_PATH}" -s {device_id} pull /sdcard/{filename} {filename}', 
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except: return None, filename

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
    log(device_id, "⚠️ KILL APP: Khởi động lại game...")
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttacticsvn")
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttactics")
    time.sleep(2)
    adb_command(device_id, "shell input keyevent 3")

# ================= 4. HÀM XỬ LÝ CHUỖI KẾT THÚC =================
def handle_end_game_sequence(device_id):
    # Hàm này giờ chỉ tập trung tìm nút Tiếp tục & Chơi lại
    # Việc bấm xác nhận đầu hàng đã được lo ở vòng lặp chính
    log(device_id, "🔄 Đang tìm nút Tiếp tục -> Chơi lại...")
    
    start_time = time.time()
    while time.time() - start_time < 20:
        screen_seq, f_seq = capture_screen(device_id)
        if screen_seq is None: continue
        
        # 1. Tìm nút CHƠI LẠI (Ưu tiên bấm luôn để thoát)
        pos_choi_lai = find_image(NUT_CHOI_LAI, screen_seq)
        if pos_choi_lai:
            log(device_id, f"🚀 Bấm CHƠI LẠI ({NUT_CHOI_LAI}) -> Xong!")
            tap(device_id, *pos_choi_lai)
            try: os.remove(f_seq); except: pass
            break 

        # 2. Tìm nút TIẾP TỤC
        pos_tiep_tuc = find_image(NUT_TIEP_TUC, screen_seq)
        if pos_tiep_tuc:
            log(device_id, f"👉 Bấm TIẾP TỤC...")
            tap(device_id, *pos_tiep_tuc)
            time.sleep(0.3)
            tap(device_id, *pos_tiep_tuc)
            start_time = time.time() # Reset timeout
            time.sleep(1)
            try: os.remove(f_seq); except: pass
            continue

        # 3. [DỰ PHÒNG] Nếu vẫn thấy Xác nhận chung (OpenGL/Confirm)
        # Thì cứ bấm tiếp, lỡ đâu lúc nãy bấm chưa ăn
        for btn_confirm in LIST_NUT_XAC_NHAN_CHUNG:
            pos_conf = find_image(btn_confirm, screen_seq)
            if pos_conf:
                log(device_id, "⚠️ Thấy nút Xác nhận -> Bấm lại.")
                tap(device_id, *pos_conf)
                time.sleep(0.5)

        # 4. Check về sảnh
        is_lobby = False
        for btn_play in LIST_NUT_VAO_TRAN:
            if find_image(btn_play, screen_seq): is_lobby = True
        if is_lobby:
            log(device_id, "✨ Đã về sảnh -> Kết thúc chuỗi.")
            try: os.remove(f_seq); except: pass
            break
        
        # 5. Check thoát thua
        for btn_exit in LIST_NUT_THOAT_THUA:
            p_exit = find_image(btn_exit, screen_seq)
            if p_exit:
                tap(device_id, *p_exit)

        try: os.remove(f_seq); except: pass
        time.sleep(0.5)

# ================= 5. LOGIC AUTO CHÍNH =================
def run_bot(device_id):
    log(device_id, "⚡ Bot Merged Function (OpenGL + Confirm): Sẵn sàng!")
    
    last_check_time = 0 
    lobby_stuck_start = 0 
    mode_spam_count = 0 
    loop_count = 0 
    
    time.sleep(random.uniform(0, 5)) 

    while True:
        try:
            loop_count += 1
            screen, filename = capture_screen(device_id)
            if screen is None:
                time.sleep(0.5)
                continue

            # --- A. XỬ LÝ NÚT XÁC NHẬN CHUNG (OPENGL / ĐẦU HÀNG) ---
            # Đây là phần GỘP CHỨC NĂNG: Thấy nút xác nhận là bấm
            found_confirm = False
            for btn_confirm in LIST_NUT_XAC_NHAN_CHUNG:
                pos_conf = find_image(btn_confirm, screen)
                if pos_conf:
                    log(device_id, f"✅ Bấm nút Xác nhận chung ({btn_confirm})")
                    tap(device_id, *pos_conf)
                    
                    # Nếu đây là nút Xác nhận đầu hàng -> Gọi chuỗi kết thúc
                    # Nếu là OpenGL -> Thì coi như tắt bảng, vòng sau chạy tiếp
                    time.sleep(1) 
                    
                    # Kiểm tra nhanh: Nếu sau khi bấm mà thấy nút Tiếp tục -> Chắc chắn là vừa đầu hàng
                    screen_check, f_check = capture_screen(device_id)
                    if screen_check is not None:
                        if find_image(NUT_TIEP_TUC, screen_check) or find_image(NUT_CHOI_LAI, screen_check):
                            handle_end_game_sequence(device_id)
                        try: os.remove(f_check); except: pass
                    
                    found_confirm = True
                    break
            if found_confirm: continue

            # --- B. CÁC LOGIC KHÁC ---
            
            # Kết nối
            if find_image(NUT_LOI_KET_NOI, screen):
                log(device_id, "❌ Lỗi kết nối -> Kill App!")
                force_stop_game(device_id)
                time.sleep(5) 
                continue
            
            # Mở game
            if find_image(ICON_GAME, screen):
                log(device_id, "♻️ Mở game -> Đợi 10s...")
                tap(device_id, *find_image(ICON_GAME, screen))
                time.sleep(10)
                # Sau 10s sẽ quay lại vòng lặp, lúc này nếu có OpenGL 
                # thì nó sẽ rơi vào mục A (Nút xác nhận chung) -> Bấm luôn.
                continue
            
            # Cập nhật
            if find_image(NUT_CAP_NHAT, screen):
                log(device_id, "⬇️ Bấm Cập nhật.")
                tap(device_id, *find_image(NUT_CAP_NHAT, screen))
                time.sleep(5)
                continue
            
            pos_thoat_capnhat = find_image(NUT_THOAT_CAP_NHAT, screen)
            if pos_thoat_capnhat:
                log(device_id, f"⚠️ Bấm Thoát Cập Nhật ({NUT_THOAT_CAP_NHAT})")
                tap(device_id, *pos_thoat_capnhat)
                time.sleep(5)
                continue

            # --- C. THOÁT TRẬN / ĐẦU HÀNG ---
            found_loss_exit = False
            for exit_img in LIST_NUT_THOAT_THUA:
                pos = find_image(exit_img, screen)
                if pos:
                    log(device_id, f"💀 Hết máu -> Bấm Exit ({exit_img})")
                    tap(device_id, *pos)
                    time.sleep(1) 
                    handle_end_game_sequence(device_id)
                    found_loss_exit = True
                    break
            if found_loss_exit: continue

            if find_image("accept.png", screen):
                tap(device_id, *find_image("accept.png", screen))
                time.sleep(1) 
                continue

            if find_image("surrender_btn.png", screen):
                tap(device_id, *find_image("surrender_btn.png", screen))
                time.sleep(0.5)
                continue
                # Bấm đầu hàng xong -> Hiện bảng xác nhận -> Vòng lặp sau sẽ vào mục A để bấm xác nhận

            if find_image("nut_doi.png", screen):
                tap(device_id, *find_image("nut_doi.png", screen))
                time.sleep(0.5)
                continue

            # --- D. TÌM TRẬN ---
            pos_play_active = None
            for btn_play in LIST_NUT_VAO_TRAN:
                pos_play_active = find_image(btn_play, screen)
                if pos_play_active: break 
            
            if not pos_play_active:
                if mode_spam_count < 2: 
                    pos_new = find_image("nut_che_do_moi.png", screen)
                    if pos_new:
                        tap(device_id, *pos_new)
                        mode_spam_count += 1
                        time.sleep(1)
                        continue
                    pos_normal = find_image("nut_che_do_thuong.png", screen)
                    if pos_normal:
                        tap(device_id, *pos_normal)
                        mode_spam_count += 1
                        time.sleep(1)
                        continue
            
            if pos_play_active:
                log(device_id, "🔥 Bấm TÌM TRẬN.")
                tap(device_id, *pos_play_active)
                time.sleep(3) 
                if lobby_stuck_start == 0: lobby_stuck_start = time.time()
                elif time.time() - lobby_stuck_start > 60:
                    log(device_id, "⚠️ Treo sảnh -> Reset.")
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

            # --- E. CỬA HÀNG & POPUP ---
            if loop_count % 3 == 0: 
                pos_store = find_image(NUT_DONG_CUA_HANG, screen)
                if pos_store:
                    log(device_id, f"🛒 Đóng cửa hàng -> Tìm Cài đặt!")
                    tap(device_id, *pos_store)
                    time.sleep(1)
                    screen_new, f_new = capture_screen(device_id)
                    if screen_new is not None:
                        settings_pos = find_image("settings_icon.png", screen_new)
                        if settings_pos: 
                            log(device_id, "⚙️ Bấm Cài đặt.")
                            tap(device_id, *settings_pos)
                        try: os.remove(f_new)
                        except: pass
                else:
                    for popup_img in LIST_POPUP_RAC:
                        popup_pos = find_image(popup_img, screen)
                        if popup_pos:
                            tap(device_id, *popup_pos)
                            time.sleep(0.5)
                            break

            # --- F. MENU CHECK ---
            current_time = time.time()
            if current_time - last_check_time > 60: 
                if not find_image("settings_icon.png", screen):
                    if find_image(NUT_DONG_CUA_HANG, screen):
                         tap(device_id, *find_image(NUT_DONG_CUA_HANG, screen))
                         time.sleep(1)
                else:
                    tap(device_id, *find_image("settings_icon.png", screen))
                last_check_time = time.time()

            try: os.remove(filename) 
            except: pass
            time.sleep(0.5)

        except Exception as e:
            log(device_id, f"LỖI: {e}")
            time.sleep(3)

def main():
    print(f"=== BOT AUTO TFT - MERGED BUTTONS ===")
    if not LIST_DEVICES: return
    threads = []
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot, args=(dev,))
        t.daemon = True 
        threads.append(t)
        t.start()
        time.sleep(2) 
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()