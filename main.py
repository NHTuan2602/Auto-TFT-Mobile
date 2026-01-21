import cv2
import numpy as np
import os
import time
import subprocess
import random

# ================= CẤU HÌNH =================
LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9" 
THRESHOLD = 0.85 

# Danh sách các nút thoát (Bạn có thể thêm nut_thoat_3.png v.v... vào đây)
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
    adb_command("shell screencap -p /sdcard/screen.png")
    adb_command("pull /sdcard/screen.png .")
    return cv2.imread("screen.png")

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
    print("--- AUTO TFT (HỖ TRỢ NHIỀU NÚT THOÁT) ---")
    print("Đang chạy...")
    
    last_check_time = 0 

    while True:
        try:
            screen = capture_screen()
            if screen is None:
                time.sleep(1)
                continue

            # ====================================================
            # 1. ƯU TIÊN CAO NHẤT: CÁC NÚT QUAN TRỌNG
            # ====================================================
            
            # [LỖI] Bấm Đợi
            wait_pos = find_image("nut_doi.png", screen)
            if wait_pos:
                print("=> [LỖI] Bấm Đợi")
                tap(*wait_pos)
                time.sleep(1)
                continue 

            # [GAME] QUÉT DANH SÁCH NÚT THOÁT (Mới)
            found_exit = False
            for exit_img in LIST_NUT_THOAT:
                exit_pos = find_image(exit_img, screen)
                if exit_pos:
                    print(f"=> [GAME] Thấy nút thoát ({exit_img}) -> Click")
                    tap(*exit_pos)
                    print("=> Về sảnh...")
                    time.sleep(8) # Chờ lâu chút để load về sảnh
                    found_exit = True
                    break # Thấy 1 nút là bấm luôn, thoát vòng lặp for
            
            if found_exit:
                continue # Quay lại đầu vòng lặp while

            # [ĐẦU HÀNG] Nút Đầu Hàng (Quét liên tục)
            sur_pos = find_image("surrender_btn.png", screen)
            if sur_pos:
                print("=> [ĐẦU HÀNG] Nút SÁNG! Bấm ngay!")
                tap(*sur_pos)
                time.sleep(1)
                
                # Xác nhận
                conf_pos = find_image("confirm_surrender.png", capture_screen())
                if conf_pos: 
                    tap(*conf_pos)
                    print("=> Đã bấm xác nhận. Đợi hiện bảng kết quả...")
                    time.sleep(10) # Đợi 10s cho bảng hiện ra
                continue

            # [SẢNH] Nút Chấp Nhận
            pos_accept = find_image("accept.png", screen)
            if pos_accept:
                print("=> [SẢNH] Bấm CHẤP NHẬN")
                tap(*pos_accept)
                last_check_time = time.time() 
                time.sleep(3) 
                continue

            # [SẢNH] Nút Tìm Trận
            pos_find = find_image("find_match.png", screen)
            if pos_find:
                print("=> [SẢNH] Bấm TÌM TRẬN")
                tap(*pos_find)
                time.sleep(3)
                continue

            # ====================================================
            # 2. HÀNH ĐỘNG ĐỊNH KỲ (MỞ MENU)
            # ====================================================
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

            # Nghỉ ngắn
            time.sleep(0.5)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()