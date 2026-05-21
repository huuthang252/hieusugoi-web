from pathlib import Path
import py_compile

root = Path(r'C:\Users\nguyen\Desktop\Project\Hieusugoi\Workspace\HIEUSU~2')
files = [root / 'main.py']
for name in ['login_window.py', 'session_manager.py', 'license_validator.py']:
    files.append(next(root.rglob(name)))
for f in files:
    print('compile', f)
    py_compile.compile(str(f), doraise=True)
print('ok')
