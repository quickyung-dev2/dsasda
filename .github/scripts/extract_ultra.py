# extract_ultra.py - Extract UltraViewer ID & PASS using pywinauto
import sys
import time
from pywinauto import Application, findwindows
from pywinauto.timings import wait_until_passes

def log(msg):
    print(msg, file=sys.stdout)
    with open("extract_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")

log("Bắt đầu extract UltraViewer ID/PASS")

try:
    # Thử connect với backend win32 (thường phù hợp UltraViewer)
    app = Application(backend='win32').connect(title_re=".*UltraViewer.*", timeout=30)
    log("Connect thành công với backend=win32")
except findwindows.ElementNotFoundError:
    try:
        # Fallback UIA nếu win32 fail
        app = Application(backend='uia').connect(title_re=".*UltraViewer.*", timeout=30)
        log("Connect thành công với backend=uia (fallback)")
    except Exception as e:
        log(f"Không connect được UltraViewer: {str(e)}")
        print("UltraViewer_ID: Unknown")
        print("UltraViewer_Password: Unknown")
        sys.exit(1)

try:
    # Lấy cửa sổ chính (thường title chứa ID)
    dlg = app.top_window()
    dlg.wait('visible ready', timeout=60)
    log("Cửa sổ chính UltraViewer đã visible")

    # Debug: Dump toàn bộ control tree ra log
    log("Dump control identifiers:")
    dlg.print_control_identifiers(file=sys.stdout)  # in ra stdout để xem log Actions

    # Tìm ID: thường là Static text kiểu "Your ID: 12345678" hoặc Edit readonly
    id_text = "Unknown"
    pass_text = "Unknown"

    # Cách 1: Tìm control chứa "ID" hoặc số dài 8-10 chữ số
    for ctrl in dlg.descendants():
        text = ctrl.window_text().strip()
        if text and len(text) >= 8 and text.isdigit():  # ID thường là số
            id_text = text
            log(f"Tìm thấy ID tiềm năng: {id_text}")
            break
        if "ID" in text.upper():
            id_text = text.split(":", 1)[-1].strip() if ":" in text else text
            log(f"Tìm thấy text chứa ID: {id_text}")

    # Cách 2: Tìm Password (thường "Password: XXXXXX" hoặc random chars)
    for ctrl in dlg.descendants():
        text = ctrl.window_text().strip()
        if "PASS" in text.upper() or (len(text) >= 6 and any(c.isupper() for c in text) and any(c.isdigit() for c in text)):
            pass_text = text.split(":", 1)[-1].strip() if ":" in text else text
            log(f"Tìm thấy PASS tiềm năng: {pass_text}")

    # Nếu vẫn Unknown, thử OCR fallback (cần pytesseract + pillow, nhưng GitHub Actions chưa install → skip tạm)
    # Hoặc dùng dlg.child_window(title_re=".*ID.*").window_text()

    print(f"UltraViewer_ID: {id_text}")
    print(f"UltraViewer_Password: {pass_text}")

except Exception as e:
    log(f"Lỗi trong quá trình extract: {str(e)}")
    print("UltraViewer_ID: Unknown")
    print("UltraViewer_Password: Unknown")

log("Kết thúc extract")
