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

# ================= 1. XỬ LÝ ĐƯỜNG DẪN & CẤU HÌNH =================
def get_app_path():
    """Lấy đường dẫn chuẩn dù chạy bằng file .py hay file .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_PATH = get_app_path()
CONFIG_FILE = os.path.join(APP_PATH, "config.json")

# Cờ để ẩn cửa sổ CMD khi gọi lệnh ngầm
NO_WINDOW_FLAG = 0x08000000 

IS_RUNNING = False  
LOG_WIDGET = None   

LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9"
ADB_PATH = "" 
THRESHOLD = 0.85
LIST_DEVICES = []

# ================= 2. TỰ ĐỘNG TÌM ADB =================
def setup_adb_path(config_ld_path):
    global ADB_PATH
    local_adb = os.path.join(APP_PATH, "adb.exe")
    if os.path.exists(local_adb):
        ADB_PATH = local_adb
        return "Local"
    
    installed_adb = os.path.join(config_ld_path, "adb.exe")
    if os.path.exists(installed_adb):
        ADB_PATH = installed_adb
        return "Installed"
        
    return "Not Found"

# ================= 3. DỮ LIỆU ẢNH =================
def get_img_path(name):
    return os.path.join(APP_PATH, name)

# --- [MỚI] Ảnh nút tắt thông báo ---
NUT_TAT_THONG_BAO = get_img_path("nut_tat_thong_bao.png")

NUT_LOI_KET_NOI = get_img_path("loi_ket_noi.png")
ICON_GAME = get_img_path("icon_game.png")
NUT_CAP_NHAT = get_img_path("nut_cap_nhat.png")
NUT_THOAT_CAP_NHAT = get_img_path("nut_thoat_1.png") 

NUT_OPENGL = get_img_path("nut_ok_opengl.png")           
NUT_XAC_NHAN_DAU_HANG = get_img_path("confirm_surrender.png") 

LIST_NUT_THOAT_THUA = [get_img_path("nut_thoat_2.png"), get_img_path("nut_thoat_chung.png")] 
NUT_TIEP_TUC = get_img_path("nut_thoat_3.png") 
NUT_CHOI_LAI = get_img_path("nut_thoat_4.png") 

NUT_DONG_CUA_HANG = get_img_path("nut_mo_rong.png") 
LIST_POPUP_RAC = [
    get_img_path("nut_dong_popup.png"), get_img_path("nut_dong_popup_1.png"),    
    get_img_path("nut_dong_popup_2.png"), get_img_path("nut_dong_popup_3.png"),
    get_img_path("nut_dong_cua_hang.png")
] 

LIST_NUT_VAO_TRAN = [get_img_path("find_match.png"), get_img_path("nut_choi_main.png")]

# ================= 4. CÁC HÀM HỖ TRỢ =================

def log(device_id, msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    text = f"[{timestamp}] [{device_id}] ➤ {msg}\n"
    print(text.strip())
    if LOG_WIDGET:
        try:
            LOG_WIDGET.configure(state='normal')
            LOG_WIDGET.insert(tk.END, text)
            LOG_WIDGET.see(tk.END)
            LOG_WIDGET.configure(state='disabled')
        except: pass

def load_config_data():
    default = {
        "LDPLAYER_PATH": r"C:\LDPlayer\LDPlayer9",
        "DEVICES": "emulator-5554\nemulator-5556"
    }
    if not os.path.exists(CONFIG_FILE):
        return default
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            dev_str = "\n".join(data.get("LIST_DEVICES", []))
            return {
                "LDPLAYER_PATH": data.get("LDPLAYER_PATH", default["LDPLAYER_PATH"]),
                "DEVICES": dev_str
            }
    except: return default

def save_config_data(path, devices_str):
    devices_list = [x.strip() for x in devices_str.split('\n') if x.strip()]
    data = {
        "LDPLAYER_PATH": path,
        "THRESHOLD": 0.85,
        "LIST_DEVICES": devices_list
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    global LDPLAYER_PATH, LIST_DEVICES
    LDPLAYER_PATH = path
    LIST_DEVICES = devices_list
    
    status = setup_adb_path(path)
    if status == "Local":
        log("SYSTEM", f"Đã nhận diện ADB đi kèm (Portable Mode).")
    elif status == "Installed":
        log("SYSTEM", f"Đã nhận diện ADB từ thư mục cài đặt.")
    else:
        log("SYSTEM", "⚠️ CẢNH BÁO: Không tìm thấy file adb.exe!")

def adb_command(device_id, cmd):
    if not IS_RUNNING or not ADB_PATH: return
    full_cmd = f'"{ADB_PATH}" -s {device_id} {cmd}'
    try:
        subprocess.run(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, creationflags=NO_WINDOW_FLAG)
    except: pass

def tap(device_id, x, y):
    if not IS_RUNNING or not ADB_PATH: return
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    full_cmd = f'"{ADB_PATH}" -s {device_id} shell input tap {rand_x} {rand_y}'
    try:
        subprocess.Popen(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=NO_WINDOW_FLAG)
    except: pass

def capture_screen(device_id):
    if not IS_RUNNING or not ADB_PATH: return None
    cmd = [ADB_PATH, "-s", device_id, "exec-out", "screencap", "-p"]
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, creationflags=NO_WINDOW_FLAG)
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

# ================= 5. LOGIC CHÍNH =================
def run_bot_logic(device_id):
    log(device_id, "⚡ Đã khởi chạy!")
    last_check_time = 0 
    loop_count = 0 
    time.sleep(random.uniform(0, 3))

    while IS_RUNNING:
        try:
            loop_count += 1
            screen = capture_screen(device_id)
            if screen is None:
                time.sleep(1)
                continue

            # --- [MỚI] CHỨC NĂNG TẮT THÔNG BÁO ---
            # Ưu tiên kiểm tra cái này đầu tiên để dọn rác màn hình
            if find_image(NUT_TAT_THONG_BAO, screen):
                log(device_id, "🚫 Phát hiện thông báo -> Tắt ngay!")
                tap(device_id, *find_image(NUT_TAT_THONG_BAO, screen))
                time.sleep(1)
                continue
            # -------------------------------------

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
                pos_new = find_image("nut_che_do_moi.png", screen)
                if pos_new:
                    tap(device_id, *pos_new)
                    time.sleep(1)
                    continue
                pos_normal = find_image("nut_che_do_thuong.png", screen)
                if pos_normal:
                    tap(device_id, *pos_normal)
                    time.sleep(1)
                    continue
            
            if pos_play_active:
                log(device_id, "🔥 Bấm TÌM TRẬN.")
                tap(device_id, *pos_play_active)
                time.sleep(5) 
                continue

            # E. POPUP & CỬA HÀNG
            if loop_count % 3 == 0: 
                pos_store = find_image(NUT_DONG_CUA_HANG, screen)
                if pos_store:
                    log(device_id, "🛒 Đóng cửa hàng")
                    tap(device_id, *pos_store)
                    time.sleep(1)
                else:
                    for popup_img in LIST_POPUP_RAC:
                        popup_pos = find_image(popup_img, screen)
                        if popup_pos:
                            tap(device_id, *popup_pos)
                            time.sleep(0.5)
                            break

            # F. CHECK MENU
            current_time = time.time()
            if current_time - last_check_time > 60: 
                if not find_image("settings_icon.png", screen):
                    if find_image(NUT_DONG_CUA_HANG, screen):
                         tap(device_id, *find_image(NUT_DONG_CUA_HANG, screen))
                         time.sleep(1)
                    elif find_image("nut_quay_lai.png", screen):
                        tap(device_id, *find_image("nut_quay_lai.png", screen))
                else:
                    tap(device_id, *find_image("settings_icon.png", screen))
                last_check_time = time.time()

            time.sleep(1)

        except Exception as e:
            log(device_id, f"LỖI: {e}")
            time.sleep(3)
    
    log(device_id, "🛑 Đã dừng.")

# ================= 6. GIAO DIỆN GUI =================
def start_auto():
    global IS_RUNNING
    if IS_RUNNING: return

    path = entry_path.get()
    devices_text = txt_devices.get("1.0", tk.END).strip()
    
    if not path or not devices_text:
        messagebox.showerror("Lỗi", "Vui lòng nhập cấu hình!")
        return

    save_config_data(path, devices_text)
    
    if not ADB_PATH:
        messagebox.showerror("Lỗi Nghiêm Trọng", f"Không tìm thấy 'adb.exe'!\nHãy copy file adb.exe vào thư mục chứa Tool này.")
        return

    IS_RUNNING = True
    btn_start.config(state="disabled", bg="#cccccc")
    btn_stop.config(state="normal", bg="#ff4444")
    
    for dev in LIST_DEVICES:
        t = threading.Thread(target=run_bot_logic, args=(dev,))
        t.daemon = True
        t.start()
        time.sleep(1)

def stop_auto():
    global IS_RUNNING
    IS_RUNNING = False
    btn_start.config(state="normal", bg="#4CAF50")
    btn_stop.config(state="disabled", bg="#cccccc")
    log("SYSTEM", "Đang dừng...")

window = tk.Tk()
window.title("AUTO TFT MOBILE - V2 (Thêm tắt thông báo)")
window.geometry("500x600")
try:
    if os.path.exists(ICON_GAME): window.iconphoto(False, tk.PhotoImage(file=ICON_GAME))
except: pass

frame_config = tk.LabelFrame(window, text="Cấu Hình", padx=10, pady=10)
frame_config.pack(fill="x", padx=10, pady=5)

tk.Label(frame_config, text="Đường dẫn LDPlayer gốc:").pack(anchor="w")
entry_path = tk.Entry(frame_config, width=50)
entry_path.pack(fill="x", pady=5)

tk.Label(frame_config, text="Danh sách thiết bị:").pack(anchor="w")
txt_devices = scrolledtext.ScrolledText(frame_config, width=40, height=6)
txt_devices.pack(fill="x", pady=5)

frame_control = tk.Frame(window)
frame_control.pack(pady=5)
btn_start = tk.Button(frame_control, text="▶ CHẠY AUTO", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=15, command=start_auto)
btn_start.pack(side="left", padx=10)
btn_stop = tk.Button(frame_control, text="⏹ DỪNG", bg="#cccccc", fg="white", font=("Arial", 11, "bold"), width=15, command=stop_auto, state="disabled")
btn_stop.pack(side="left", padx=10)

tk.Label(window, text="Nhật ký hoạt động:").pack(anchor="w", padx=10)
LOG_WIDGET = scrolledtext.ScrolledText(window, width=58, height=15, state='disabled', bg="#f0f0f0")
LOG_WIDGET.pack(padx=10, pady=5)

saved_data = load_config_data()
entry_path.insert(0, saved_data["LDPLAYER_PATH"])
txt_devices.insert(tk.END, saved_data["DEVICES"])

setup_adb_path(saved_data["LDPLAYER_PATH"])

window.mainloop()