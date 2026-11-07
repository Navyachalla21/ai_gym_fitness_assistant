"""Run once from the streamlit_dashboard folder:  python patch_app.py
Turns the top tab bar into the sidebar-driven module picker. A backup app_backup.py is saved first."""
import re, shutil
src = open("app.py", encoding="utf-8").read()
shutil.copy("app.py", "app_backup.py")

n_tabs = len(re.findall(r"^tabs\s*=\s*st\.tabs\(", src, flags=re.M))
src = re.sub(r"^tabs\s*=\s*st\.tabs\(.*?\)\s*$", '_sel = st.session_state.get("module", 0)', src, count=1, flags=re.M | re.S)
src, n_with = re.subn(r"^(\s*)with tabs\[(\d)\]:", r"\1if _sel == \2:", src, flags=re.M)
open("app.py", "w", encoding="utf-8").write(src)
print(f"tab bar replaced: {n_tabs}, module blocks converted: {n_with} (expected 7)")
