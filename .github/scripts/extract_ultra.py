# extract_ultra.py - Fix Unicode + Extract UltraViewer ID & PASS
import sys
import time
import re
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError, WindowAmbiguousError

# Fix UnicodeEncodeError: Force stdout UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    # Python < 3.7 fallback
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S UTC')
    safe_msg = msg.encode('utf-8', errors='replace').decode('utf-8')  # safe
    print(f"[{ts}] {safe_msg}")
    # Append to file (luôn an toàn)
    with open("extract_debug.log", "a", encoding="utf-8", errors='replace') as f:
        f.write(f"[{ts}] {safe_msg}\n")

log("START: Extract UltraViewer ID & PASS (UTF-8 fixed)")

app = None
for bk in ['win32', 'uia']:
    try:
        log(f"Thử backend '{bk}' (timeout 60s)")
        app = Application(backend=bk).connect(title_re=r".*UltraViewer.*", timeout=60)
        log(f"CONNECTED với '{bk}'")
        break
    except Exception as e:
        log(f"Backend '{bk}' fail: {str(e)}")

if not app:
    log("Không connect được UltraViewer!")
    print("ID: Unknown | PASS: Unknown")
    sys.exit(0)

try:
    dlg = app.top_window()
    log("Chờ window visible & ready (90s)")
    dlg.wait('visible ready enabled', timeout=90)

    title = dlg.window_text() or ""
    log(f"Window title: {title}")

    # Dump UI tree vào FILE thay vì print trực tiếp (tránh Unicode crash)
    dump_path = "ui_dump.txt"
    log(f"Dump UI tree vào file: {dump_path}")
    with open(dump_path, "w", encoding="utf-8", errors='replace') as f:
        dlg.print_control_identifiers(file=f, depth=10)
    # In excerpt nhỏ để log
    with open(dump_path, "r", encoding="utf-8", errors='replace') as f:
        excerpt = f.read(2000)  # giới hạn tránh log quá dài
        print("UI Dump excerpt (first 2000 chars):\n" + excerpt)

    id_val = "Unknown"
    pass_val = "Unknown"

    # Parse từ title
    id_match = re.search(r'\b\d{9}\b', title)
    if id_match:
        id_val = id_match.group(0)
        log(f"ID từ title: {id_val}")

    # Duyệt controls (Static/Text/Edit)
    for ctrl in dlg.descendants():
        try:
            text = (ctrl.window_text() or "").strip()
            if not text:
                continue

            # ID: chính xác 9 số
            if re.fullmatch(r'\d{9}', text):
                id_val = text
                log(f"ID từ control: {text}")

            # PASS: 6-8 ký tự mix (thường random)
            if 6 <= len(text) <= 8 and any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
                pass_val = text
                log(f"PASS tiềm năng: {text}")

            # Nếu label có "ID" / "Mã" / "Your ID" / "ID của bạn"
            if re.search(r'(ID|Mã|Your ID|ID của bạn)', text, re.I):
                try:
                    sib = ctrl.next_sibling_control()
                    if sib:
                        sib_text = sib.window_text().strip()
                        if re.fullmatch(r'\d{9}', sib_text):
                            id_val = sib_text
                            log(f"ID từ sibling: {sib_text}")
                except:
                    pass

            # Label "Password" / "Mật khẩu" / "Pass"
            if re.search(r'(Password|Mật khẩu|Pass)', text, re.I):
                try:
                    sib = ctrl.next_sibling_control()
                    if sib:
                        sib_text = sib.window_text().strip()
                        if 6 <= len(sib_text) <= 8:
                            pass_val = sib_text
                            log(f"PASS từ sibling: {sib_text}")
                except:
                    pass

    # Fallback từ dump file
    with open(dump_path, "r", encoding="utf-8", errors='replace') as f:
        dump_content = f.read()
    if id_val == "Unknown":
        m = re.search(r'\b\d{9}\b', dump_content)
        if m:
            id_val = m.group(0)
            log(f"ID fallback từ dump: {id_val}")
    if pass_val == "Unknown":
        m = re.search(r'\b([A-Za-z0-9]{6,8})\b', dump_content)
        if m:
            pass_val = m.group(1)
            log(f"PASS fallback từ dump: {pass_val}")

    # Kết quả chính
    print(f"\n=== FINAL ID & PASS ===\nID: {id_val}\nPASS: {pass_val}\n===================\n")

except Exception as e:
    log(f"ERROR extract: {str(e)}")
    print("ID: Unknown | PASS: Unknown")

log("END: Extract done")
