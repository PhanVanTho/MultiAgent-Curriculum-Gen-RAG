import re

with open('ung_dung.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add the route
route_code = """
@app.post("/huy/<ma_cv>")
def huy_giao_trinh(ma_cv):
    if ma_cv in CONG_VIEC:
        CONG_VIEC[ma_cv]["huy_bo"] = True
        return {"status": "success", "message": "Đã gửi lệnh hủy"}
    return {"status": "error", "message": "Không tìm thấy tiến trình"}, 404
"""

if "/huy/<ma_cv>" not in code:
    code = code.replace('@app.post("/tao")', route_code + '\n@app.post("/tao")')

# Inject check_cancel() definition
check_cancel_def = """                def check_cancel():
                    if CONG_VIEC.get(ma_cv, {}).get("huy_bo"):
                        raise Exception("Tiến trình đã bị người dùng hủy.")
"""
if "def check_cancel():" not in code:
    code = code.replace('                meta_controller_instance.reset_state()', '                meta_controller_instance.reset_state()\n' + check_cancel_def)

# Inject check_cancel() at key points
points = [
    'CONG_VIEC[ma_cv].update({"tien_do": 10',
    'CONG_VIEC[ma_cv].update({"tien_do": 50',
    'CONG_VIEC[ma_cv].update({"tien_do": 60',
    'CONG_VIEC[ma_cv].update({"tien_do": 70',
    'CONG_VIEC[ma_cv].update({"tien_do": 85'
]

lines = code.split('\n')
for i, line in enumerate(lines):
    if any(p in line for p in points) and "check_cancel()" not in lines[i-1]:
        indent = len(line) - len(line.lstrip())
        lines[i] = " " * indent + "check_cancel()\n" + line

with open('ung_dung.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("Added check_cancel logic to ung_dung.py")
