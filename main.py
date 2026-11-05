import os
import sqlite3
import sys
from datetime import datetime
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)
DB = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "lost_items.db"))

with sqlite3.connect(DB) as db:
    db.execute("CREATE TABLE IF NOT EXISTS items (name, place, description, contact, date)")

PAGE = """
<h1>분실물 찾기</h1>
<form method="post">
  <input name="name" placeholder="물건 이름" required>
  <input name="place" placeholder="습득 장소" required>
  <input name="description" placeholder="특징" required>
  <input name="contact" placeholder="연락 방법" required>
  <button>등록</button>
</form>
<h2>분실물 목록</h2>
{% for item in items %}
  <p><b>{{ item[0] }}</b><br>등록번호: {{ item[5] }}<br>습득 장소 : {{ item[1] }}<br>특징 : {{ item[2] }}<br>연락: {{ item[3] }}<br>등록 일자 : {{ item[4] }}</p>
{% else %}<p>등록된 분실물이 없습니다.</p>{% endfor %}
"""


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        fields = [request.form[key].strip() for key in ("name", "place", "description", "contact")]
        with sqlite3.connect(DB) as db:
            db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", (*fields, datetime.now().strftime("%Y-%m-%d %H:%M")))
        return redirect("/")

    with sqlite3.connect(DB) as db:
        items = db.execute("SELECT *, rowid FROM items ORDER BY rowid DESC").fetchall()
    return render_template_string(PAGE, items=items)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "delete":
        with sqlite3.connect(DB) as db:
            result = db.execute("DELETE FROM items WHERE rowid = ?", (sys.argv[2],))
        print("Deleted." if result.rowcount else "ID not found.")
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
