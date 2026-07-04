#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Desktop側リポジトリ用:
web/app.py に /mobile を追加します。
Windows側の hoshinoyakata_allsky_agent フォルダ直下で実行してください。
"""

from pathlib import Path
from datetime import datetime
import shutil
import re
import py_compile
import sys

base = Path.cwd()
app = base / "web" / "app.py"
mobile = base / "web" / "templates" / "mobile.html"

if not app.exists():
    print("ERROR: web/app.py が見つかりません。hoshinoyakata_allsky_agent フォルダ直下で実行してください。")
    sys.exit(1)

if not mobile.exists():
    print("ERROR: web/templates/mobile.html が見つかりません。先に mobile.html を web/templates にコピーしてください。")
    sys.exit(1)

text = app.read_text(encoding="utf-8")

if "@app.route('/mobile')" in text or '@app.route("/mobile")' in text:
    print("OK: /mobile はすでに app.py に入っています。")
else:
    backup = app.with_name("app.py.backup_mobile_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(app, backup)
    print("backup:", backup)

    if "render_template" not in text:
        def repl(m):
            imports = m.group(1).strip()
            names = [x.strip() for x in imports.split(",")]
            if "render_template" not in names:
                names.append("render_template")
            return "from flask import " + ", ".join(names)
        text = re.sub(r"from\s+flask\s+import\s+([^\n]+)", repl, text, count=1)

    route = """

@app.route('/mobile')
def mobile_view():
    return render_template('mobile.html')
"""

    marker = "\n@app.route('/api/status')"
    if marker in text:
        text = text.replace(marker, route + marker, 1)
    else:
        marker2 = "\nif __name__"
        if marker2 in text:
            text = text.replace(marker2, route + marker2, 1)
        else:
            text = text.rstrip() + route + "\n"

    app.write_text(text, encoding="utf-8")
    print("OK: /mobile を app.py に追加しました。")

try:
    py_compile.compile(str(app), doraise=True)
    print("OK: app.py Python構文チェック成功")
except Exception as e:
    print("ERROR: app.py 構文チェック失敗")
    print(e)
    sys.exit(1)

print("次: GitHub Desktopで変更を Commit to main → Push origin")
