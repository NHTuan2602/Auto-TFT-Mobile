import cv2
import numpy as np
import os
import time
import subprocess
import random
import threading
import json
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox
import sys

# ================= 1. CẤU HÌNH & BIẾN TOÀN CỤC =================
CONFIG_FILE = "config.json"
IS_RUNNING = False  # Biến kiểm soát trạng thái chạy/dừng
LOG_WIDGET = None   # Biến để hứng widget log giao diện

# Các biến cấu hình mặc định
LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9"
ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")
THRESHOLD = 0.85
LIST_DEVICES = []

# ================= 2. DỮ LIỆU ẢNH MẪU =================
NUT_LOI_KET_NOI = "loi_ket_noi.png"
ICON_GAME = "icon_game.png"
NUT_CAP_NHAT = "nut_cap_nhat.png"
NUT_THOAT_CAP_NHAT = "nut_thoat_1.png" 

NUT_OPENGL = "nut_ok_opengl.png"           
NUT_XAC_NHAN_DAU_HANG = "confirm_surrender.png" 

LIST_NUT_THOAT_THUA = ["nut_thoat_2.png", "nut_thoat_chung.png"] 
NUT_TIEP_TUC = "nut_thoat_3.png" 
NUT_CHOI_LAI = "nut_thoat_4.png" 

NUT_DONG_CUA_HANG = "nut_mo_rong.png" 
LIST_POPUP_RAC = [
    "nut_dong_popup.png", "nut_dong_popup_1.png",    
    "nut_dong_popup_2.png", "nut_dong_popup_3.png",
    "nut_dong_cua_hang.png"
] 

LIST_NUT_VAO_TRAN = ["find_match.png", "nut_choi_main.png"]

# ================= 3. CÁC HÀM HỖ TRỢ LOGIC =================

def log(device_id, msg):
    """Ghi log ra giao diện thay vì CMD"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    text = f"[{timestamp}] [{device_id}] ➤ {msg}\n"
    print(text.strip()) # Vẫn in ra CMD để debug nếu cần
    
    if LOG_WIDGET:
        try:
            LOG_WIDGET.configure(state='normal')
            LOG_WIDGET.insert(tk.END, text)
            LOG_WIDGET.see(tk.END) # Tự cuộn xuống dưới cùng
            LOG_WIDGET.configure(state='disabled')
        except: pass

def load_config_data():
    """Đọc file config để hiển thị lên giao diện lúc mở app"""
    default = {
        "LDPLAYER_PATH": r"C:\LDPlayer\LDPlayer9",
        "DEVICES": "emulator-5554\nemulator-5556"
    }
    if not os.path.exists(CONFIG_FILE):
        return default
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Chuyển list thiết bị thành chuỗi xuống dòng để hiện trong text box
            dev_str = "\n".join(data.get("LIST_DEVICES", []))
            return {
                "LDPLAYER_PATH": data.get("LDPLAYER_PATH", default["LDPLAYER_PATH"]),
                "DEVICES": dev_str
            }
    except: return default

def save_config_data(path, devices_str):
    """Lưu cấu hình từ giao diện xuống file"""
    devices_list = [x.strip() for x in devices_str.split('\n') if x.strip()]
    data = {
        "LDPLAYER_PATH": path,
        "THRESHOLD": 0.85,
        "LIST_DEVICES": devices_list
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    # Cập nhật biến toàn cục
    global LDPLAYER_PATH, ADB_PATH, LIST_DEVICES
    LDPLAYER_PATH = path
    ADB_PATH = os.path.join(path, "adb.exe")
    LIST_DEVICES = devices_list

# --- Các hàm ADB & Xử lý ảnh (Giữ nguyên tối ưu CPU) ---
def adb_command(device_id, cmd):
    if not IS_RUNNING: return
    full_cmd = f'"{ADB_PATH}" -s {device_id} {cmd}'
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except: pass

def tap(device_id, x, y):
    if not IS_RUNNING: return
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    full_cmd = f'"{ADB_PATH}" -s {device_id} shell input tap {rand_x} {rand_y}'
    try:
        subprocess.Popen(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass

def capture_screen(device_id):
    if not IS_RUNNING: return None
    cmd = [ADB_PATH, "-s", device_id, "exec-out", "screencap", "-p"]
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        if process.returncode == 0 and process.stdout:
            return cv2.imdecode(np.frombuffer(process.stdout, np.uint8), cv2.IMREAD_COLOR)
    except: pass
    return None

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
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    except: pass
    return None

def force_stop_game(device_id):
    log(device_id, "⚠️ KILL APP...")
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttacticsvn")
    adb_command(device_id, "shell am force-stop com.riotgames.league.teamfighttactics")
    time.sleep(2)
    adb_command(device_id, "shell input keyevent 3")

def handle_end_game_sequence(device_id):
    log(device_id, "🔄 Kết thúc trận: Tìm Tiếp tục -> Chơi lại...")
    start_time = time.time()
    while IS_RUNNING and time.time() - start_time < 20:
        screen_seq = capture_screen(device_id)
        if screen_seq is None: 
            time.sleep(0.5)
            continue
        
        pos_choi_lai = find_image(NUT_CHOI_LAI, screen_seq)
        if pos_choi_lai:
            log(device_id, f"🚀 Bấm CHƠI LẠI -> Xong!")
            tap(device_id, *pos_choi_lai)
            break 

        pos_tiep_tuc = find_image(NUT_TIEP_TUC, screen_seq)
        if pos_tiep_tuc:
            log(device_id, f"👉 Bấm TIẾP TỤC...")
            tap(device_id, *pos_tiep_tuc)
            time.sleep(0.3)
            tap(device_id, *pos_tiep_tuc)
            start_time = time.time() 
            time.sleep(1)
            continue

        pos_confirm = find_image(NUT_XAC_NHAN_DAU_HANG, screen_seq)
        if pos_confirm:
            tap(device_id, *pos_confirm)
            time.sleep(0.5)

        is_lobby = False
        for btn_play in LIST_NUT_VAO_TRAN:
            if find_image(btn_play, screen_seq): is_lobby = True
        if is_lobby: break
        
        for btn_exit in LIST_NUT_THOAT_THUA:
            p_exit = find_image(btn_exit, screen_seq)
            if p_exit: tap(device_id, *p_exit)

        time.sleep(0.5)

# ================= 4. LOGIC CHÍNH CỦA BOT =================
def run_bot_logic(device_id):
    log(device_id, "⚡ Đã khởi chạy!")
    last_check_time = 0 
    lobby_stuck_start = 0 
    mode_spam_count = 0 
    loop_count = 0 
    
    time.sleep(random.uniform(0, 3)) # Delay ngẫu nhiên lúc đầu

    while IS_RUNNING:
        try:
            loop_count += 1
            screen = capture_screen(device_id)
            if screen is None:
                time.sleep(1)
                continue

            # A. HỆ THỐNG
            if find_image(NUT_OPENGL, screen):
                log(device_id, "⚠️ Bấm OK OpenGL!")
                tap(device_id, *find_image(NUT_OPENGL, screen))
                time.sleep(2) 
                continue

            if find_image(NUT_LOI_KET_NOI, screen):
                log(device_id, "❌ Lỗi kết nối -> Kill App!")
                force_stop_game(device_id)
                time.sleep(5) 
                continue
            
            if find_image(ICON_GAME, screen):
                log(device_id, "♻️ Mở game...")
                tap(device_id, *find_image(ICON_GAME, screen))
                time.sleep(10)
                continue
            
            if find_image(NUT_CAP_NHAT, screen):
                log(device_id, "⬇️ Bấm Cập nhật.")
                tap(device_id, *find_image(NUT_CAP_NHAT, screen))
                time.sleep(5)
                continue
            
            if find_image(NUT_THOAT_CAP_NHAT, screen):
                tap(device_id, *find_image(NUT_THOAT_CAP_NHAT, screen))
                time.sleep(5)
                continue

            # B. KẾT THÚC
            if find_image(NUT_TIEP_TUC, screen):
                handle_end_game_sequence(device_id)
                continue

            found_loss = False
            for exit_img in LIST_NUT_THOAT_THUA:
                pos = find_image(exit_img, screen)
                if pos:
                    log(device_id, "💀 Hết máu -> Thoát")
                    tap(device_id, *pos)
                    time.sleep(1)
                    handle_end_game_sequence(device_id)
                    found_loss = True
                    break
            if found_loss: continue

            if find_image(NUT_XAC_NHAN_DAU_HANG, screen):
                log(device_id, "🏳️ Xác nhận đầu hàng.")
                tap(device_id, *find_image(NUT_XAC_NHAN_DAU_HANG, screen))
                time.sleep(1) 
                handle_end_game_sequence(device_id)
                continue

            # C. TRONG GAME
            if find_image("surrender_btn.png", screen):
                tap(device_id, *find_image("surrender_btn.png", screen))
                time.sleep(0.5)
                continue 

            if find_image("accept.png", screen):
                tap(device_id, *find_image("accept.png", screen))
                time.sleep(1) 
                continue

            if find_image("nut_doi.png", screen):
                tap(device_id, *find_image("nut_doi.png", screen))
                time.sleep(0.5)
                continue

            # D. TÌM TRẬN
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

            # E. POPUP
            if loop_count % 3 == 0: 
                pos_store = find_image(NUT_DONG_CUA_HANG, screen)
                if pos_store:
                    log(device_id, "🛒 Đóng cửa hàng -> Cài đặt")
                    tap(device_id, *pos_store)
                    time.sleep(1)
                    screen_new = capture_screen(device_id)
                    if screen_new is not None:
                        settings_pos = find_image("settings_icon.png", screen_new)
                        if settings_pos: tap(device_id, *settings_pos)
                else:
                    for popup_img in LIST_POPUP_RAC:
                        popup_pos = find_image(popup_img, screen)
                        if popup_pos:
                            tap(device_id, *popup_pos)
                            time.sleep(0.5)
                            break

            # F. MENU CHECK
            current_time = time.time()
            if current_time - last_check_time > 60: 
                if not find_image("settings_icon.png", screen):
                    if find_image(NUT_DONG_CUA_HANG, screen):
                         tap(device_id, *find_image(NUT_DONG_CUA_HANG, screen))
                         time.sleep(1)
                else:
                    tap(device_id, *find_image("settings_icon.png", screen))
                last_check_time = time.time()

            time.sleep(1)

        except Exception as e:
            log(device_id, f"LỖI: {e}")
            time.sleep(3)
    
    log(device_id, "🛑 Đã dừng luồng.")

# ================= 6. GIAO DIỆN NGƯỜI DÙNG (GUI) =================
def start_auto():
    global IS_RUNNING
    if IS_RUNNING:
        messagebox.showwarning("Chú ý", "Auto đang chạy rồi!")
        return

    path = entry_path.get()
    devices_text = txt_devices.get("1.0", tk.END).strip()
    
    if not path or not devices_text:
        messagebox.showerror("Lỗi", "Vui lòng nhập đường dẫn LDPlayer và danh sách thiết bị.")
        return

    # Lưu cấu hình và cập nhật biến toàn cục
    save_config_data(path, devices_text)
    
    IS_RUNNING = True
    btn_start.config(state="disabled", bg="#cccccc")
    btn_stop.config(state="normal", bg="#ff4444")
    
    # Chạy từng thiết bị trên 1 luồng riêng
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot_logic, args=(dev,))
        t.daemon = True
        t.start()
        time.sleep(1) # Khởi động so le tránh lag máy

def stop_auto():
    global IS_RUNNING
    IS_RUNNING = False
    btn_start.config(state="normal", bg="#4CAF50")
    btn_stop.config(state="disabled", bg="#cccccc")
    log("SYSTEM", "Đang gửi lệnh dừng cho tất cả thiết bị...")

# --- Xây dựng cửa sổ ---
window = tk.Tk()
window.title("AUTO TFT MOBILE - 6 TAB")
window.geometry("500x600")
window.resizable(False, False)

# 1. Khu vực cấu hình
frame_config = tk.LabelFrame(window, text="Cấu Hình", padx=10, pady=10)
frame_config.pack(fill="x", padx=10, pady=5)

tk.Label(frame_config, text="Đường dẫn thư mục LDPlayer:").pack(anchor="w")
entry_path = tk.Entry(frame_config, width=50)
entry_path.pack(fill="x", pady=5)

tk.Label(frame_config, text="Danh sách thiết bị (Mỗi tên 1 dòng):").pack(anchor="w")
txt_devices = scrolledtext.ScrolledText(frame_config, width=40, height=6)
txt_devices.pack(fill="x", pady=5)

# 2. Khu vực điều khiển
frame_control = tk.Frame(window)
frame_control.pack(pady=5)

btn_start = tk.Button(frame_control, text="▶ CHẠY AUTO", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=15, command=start_auto)
btn_start.pack(side="left", padx=10)

btn_stop = tk.Button(frame_control, text="⏹ DỪNG", bg="#cccccc", fg="white", font=("Arial", 12, "bold"), width=15, command=stop_auto, state="disabled")
btn_stop.pack(side="left", padx=10)

# 3. Khu vực Log
tk.Label(window, text="Nhật ký hoạt động:").pack(anchor="w", padx=10)
LOG_WIDGET = scrolledtext.ScrolledText(window, width=58, height=15, state='disabled', bg="#f0f0f0")
LOG_WIDGET.pack(padx=10, pady=5)

# --- Load dữ liệu cũ ---
saved_data = load_config_data()
entry_path.insert(0, saved_data["LDPLAYER_PATH"])
txt_devices.insert(tk.END, saved_data["DEVICES"])

# --- Chạy App ---
window.mainloop()