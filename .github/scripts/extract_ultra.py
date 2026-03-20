import time
from pywinauto import Application
import re

print("=== DEBUG ULTRAVIEWER EXTRACTION START ===")

try:
    app = Application(backend="uia").connect(title_re=".*UltraViewer.*", timeout=180)
    dlg = app.top_window()
    print("Connected to window:", dlg.window_text())

    # Dump controls
    dlg.print_control_identifiers()

    id_found = "Không lấy được"
    pass_found = "Không lấy được"

    # Duyệt tất cả descendants để tìm title chứa ID/Pass
    for child in dlg.descendants():
        try:
            title = child.window_text().strip()
            if title:
                print(f"Control title found: '{title}'")
                # ID: 9 chữ số (có space hoặc không)
                if re.search(r'\b\d{3}\s*\d{3}\s*\d{3}\b', title):
                    id_found = re.sub(r'\s+', '', title)
                    print(f"→ ID extracted: {id_found}")
                # Pass: 4-6 chữ số
                elif re.match(r'^\d{4,6}$', title):
                    pass_found = title
                    print(f"→ Password extracted: {pass_found}")
        except:
            pass

    # Fallback toàn bộ text nếu chưa tìm thấy
    if id_found == "Không lấy được" or pass_found == "Không lấy được":
        all_text = " ".join([c.window_text().strip() for c in dlg.descendants() if c.window_text().strip()])
        print("Fallback all text:", all_text)
        id_match = re.search(r'(\d{3}\s*\d{3}\s*\d{3})', all_text)
        pass_match = re.search(r'\b(\d{4,6})\b', all_text)
        if id_match:
            id_found = id_match.group(1).replace(" ", "")
        if pass_match:
            pass_found = pass_match.group(1)

    print(f"UltraViewer_ID: {id_found}")
    print(f"UltraViewer_Password: {pass_found}")

except Exception as e:
    print("LỖI pywinauto:", str(e))
    print("UltraViewer_ID: Không lấy được")
    print("UltraViewer_Password: Không lấy được")

print("=== DEBUG ULTRAVIEWER EXTRACTION END ===")
