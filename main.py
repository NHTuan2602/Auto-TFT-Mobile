import cv2
import numpy as np
import os
import time
import subprocess
import random

# ================= CẤU HÌNH =================
LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9" 
THRESHOLD = 0.85 
LIST_NUT_THOAT = ["nut_thoat_1.png", "nut_thoat_2.png"] 
# ============================================

ADB_PATH = os.path.join(LDPLAYER_PATH, "adb.exe")

def adb_command(cmd):
    full_cmd = f'"{ADB_PATH}" {cmd}'
    subprocess.call(full_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def tap(x, y):
    rand_x = x + random.randint(-5, 5)
    rand_y = y + random.randint(-5, 5)
    print(f"[CLICK] Tọa độ: {rand_x}, {rand_y}")
    adb_command(f"shell input tap {rand_x} {rand_y}")

def capture_screen():
    """Chụp ảnh an toàn (Fix lỗi can't open/read file)"""
    filename = "screen.png"
    
    # Xóa ảnh cũ
    if os.path.exists(filename):
        try: os.remove(filename)
        except: pass

    adb_command(f"shell screencap -p /sdcard/{filename}")
    adb_command(f"pull /sdcard/{filename} {filename}")
    
    # Kiểm tra file có tồn tại không
    if os.path.exists(filename):
        try:
            img = cv2.imread(filename)
            if img is not None:
                return img
        except: pass
    return None

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

def main():
    print("--- AUTO TFT (SINGLE TAB - FULL AUTO) ---")
    print("Đang chạy...")
    
    last_check_time = 0 

    while True:
        try:
            screen = capture_screen()
            if screen is None:
                time.sleep(1)
                continue

            # ================= LOGIC AUTO =================

            # 1. MÀN HÌNH CHỜ & CẬP NHẬT (Ưu tiên cao nhất)
            
            # [MỚI] Nút CHƠI ở màn hình chính -> Bấm vào
            pos_main_play = find_image("nut_choi_main.png", screen)
            if pos_main_play:
                print("=> [MAIN] Thấy nút CHƠI -> Vào sảnh.")
                tap(*pos_main_play)
                time.sleep(5) 
                continue

            # [MỚI] Chọn chế độ Thường
            pos_normal = find_image("nut_che_do_thuong.png", screen)
            if pos_normal:
                print("=> [SẢNH] Chọn chế độ Thường")
                tap(*pos_normal)
                time.sleep(1)
                continue

            # Xử lý OpenGL
            opengl_pos = find_image("nut_ok_opengl.png", screen)
            if opengl_pos:
                print("=> [OPENGL] Bấm OK bỏ qua")
                tap(*opengl_pos)
                time.sleep(2)
                continue

            # Xử lý Cập nhật
            update_pos = find_image("nut_cap_nhat.png", screen)
            if update_pos:
                print("=> [UPDATE] Thấy bản cập nhật! Bấm ngay.")
                tap(*update_pos)
                print("=> Đang tải update... Ngủ 60s...")
                time.sleep(60) 
                continue

            # Xử lý vào lại game sau update
            play_pos = find_image("nut_mo_game.png", screen)
            if play_pos:
                print("=> [UPDATE XONG] Vào lại game.")
                tap(*play_pos)
                time.sleep(20) 
                continue

            # 2. XỬ LÝ LỖI TREO
            wait_pos = find_image("nut_doi.png", screen)
            if wait_pos:
                print("=> [LỖI] Bấm Đợi")
                tap(*wait_pos)
                time.sleep(1)
                continue 

            # 3. TRONG GAME (Thoát & Đầu hàng)
            found_exit = False
            for exit_img in LIST_NUT_THOAT:
                exit_pos = find_image(exit_img, screen)
                if exit_pos:
                    print(f"=> [GAME] Thấy nút thoát ({exit_img}) -> Click")
                    tap(*exit_pos)
                    print("=> Về sảnh...")
                    time.sleep(8)
                    found_exit = True
                    break 
            if found_exit: continue

            sur_pos = find_image("surrender_btn.png", screen)
            if sur_pos:
                print("=> [ĐẦU HÀNG] Nút SÁNG! Bấm ngay!")
                tap(*sur_pos)
                time.sleep(1)
                
                conf_pos = find_image("confirm_surrender.png", capture_screen())
                if conf_pos: 
                    tap(*conf_pos)
                    print("=> Đã bấm xác nhận. Đợi...")
                    time.sleep(10)
                continue

            # 4. SẢNH CHỜ
            pos_accept = find_image("accept.png", screen)
            if pos_accept:
                print("=> [SẢNH] Bấm CHẤP NHẬN")
                tap(*pos_accept)
                last_check_time = time.time() 
                time.sleep(3) 
                continue

            pos_find = find_image("find_match.png", screen)
            if pos_find:
                print("=> [SẢNH] Bấm TÌM TRẬN")
                tap(*pos_find)
                time.sleep(3)
                continue

            # 5. MENU CHECK (Chống kẹt)
            current_time = time.time()
            if current_time - last_check_time > 20: 
                print("=> [CHECK] Mở menu để kiểm tra...")
                
                gear_pos = find_image("settings_icon.png", screen)
                
                if not gear_pos:
                    expand_pos = find_image("nut_mo_rong.png", screen)
                    if expand_pos:
                        print("-> Bấm mở rộng...")
                        tap(*expand_pos)
                        time.sleep(1) 
                else:
                    print("-> Bấm bánh răng")
                    tap(*gear_pos)

                last_check_time = time.time()

            time.sleep(0.5)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()