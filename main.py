import os
import sqlite3
import sys
from datetime import datetime
from flask import Flask, request, redirect, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lost_items.db"))

with sqlite3.connect(DB) as db:
    db.execute("CREATE TABLE IF NOT EXISTS items (name, place, description, contact, date, password_hash)")
    columns = [row[1] for row in db.execute("PRAGMA table_info(items)")]
    if "password_hash" not in columns:
        db.execute("ALTER TABLE items ADD COLUMN password_hash TEXT")

PAGE = """
<h1>분실물 찾기 서비스</h1>
<form method="post">
  <input name="name" placeholder="물건 이름" required>
  <input name="place" placeholder="습득 장소" required>
  <input name="description" placeholder="특징" required>
  <input name="contact" placeholder="연락 방법" required>
  <input type="password" name="password" placeholder="삭제 비밀번호 (4자 이상)" minlength="4" required>
  <button>등록</button>
</form>
<h2>분실물 목록</h2>
{% if error %}<p style="color: red;">삭제 비밀번호가 틀렸습니다. 다시 확인해 주세요.</p>{% endif %}
{% for item in items %}
  <p><b>{{ item[0] }}</b><br>등록번호: {{ item[5] }}<br>습득 장소 : {{ item[1] }}<br>특징 : {{ item[2] }}<br>연락 방법 : {{ item[3] }}<br>등록 일자 : {{ item[4] }}</p>
  {% if item[6] %}
  <form method="post" action="{{ url_for('delete_post', item_id=item[5]) }}">
    <input type="password" name="password" placeholder="삭제 비밀번호" required>
    <button type="submit">이 게시물 삭제</button>
  </form>
  {% else %}<small>이전 게시물은 삭제 비밀번호가 설정되어 있지 않습니다.</small>{% endif %}
{% else %}<p>등록된 분실물이 없습니다.</p>{% endfor %}
"""


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        fields = [request.form[key].strip() for key in ("name", "place", "description", "contact")]
        password = request.form.get("password", "")
        if len(password) < 4:
            return "삭제 비밀번호는 4자 이상 입력해 주세요.", 400
        with sqlite3.connect(DB) as db:
            db.execute(
                "INSERT INTO items (name, place, description, contact, date, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (*fields, datetime.now().strftime("%Y-%m-%d %H:%M"), generate_password_hash(password)),
            )
        return redirect("/")

    with sqlite3.connect(DB) as db:
        items = db.execute("SELECT name, place, description, contact, date, rowid, password_hash FROM items ORDER BY rowid DESC").fetchall()
    return render_template_string(PAGE, items=items, error=request.args.get("error"))


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_post(item_id):
    password = request.form.get("password", "")
    with sqlite3.connect(DB) as db:
        row = db.execute("SELECT password_hash FROM items WHERE rowid = ?", (item_id,)).fetchone()
        if row is None:
            return "게시물을 찾을 수 없습니다.", 404
        if not row[0] or not check_password_hash(row[0], password):
            return redirect("/?error=wrong")
        db.execute("DELETE FROM items WHERE rowid = ?", (item_id,))
    return redirect("/")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "delete":
        with sqlite3.connect(DB) as db:
            result = db.execute("DELETE FROM items WHERE rowid = ?", (sys.argv[2],))
        print("Deleted." if result.rowcount else "ID not found.")
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
