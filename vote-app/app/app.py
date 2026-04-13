from flask import Flask, request, redirect, url_for, render_template_string
import os
import time
import pymysql

app = Flask(__name__)

MYSQL_HOST = os.getenv("MYSQL_HOST", "db")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "vote_db")
MYSQL_USER = os.getenv("MYSQL_USER", "vote_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "vote_pass")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>동물 투표</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f7f7f7;
        }
        .container {
            max-width: 640px;
            margin: 0 auto;
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        h1, h2 {
            margin-top: 0;
        }
        .radio-group {
            margin: 20px 0;
        }
        .radio-item {
            margin-bottom: 12px;
            font-size: 18px;
        }
        .buttons {
            margin-top: 20px;
        }
        button {
            padding: 10px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            background-color: #2563eb;
            color: white;
            font-size: 14px;
        }
        button:hover {
            opacity: 0.9;
        }
        .result-box {
            margin-top: 24px;
            padding: 16px;
            background: #f1f5f9;
            border-radius: 8px;
        }
        .message {
            margin-top: 16px;
            color: #16a34a;
            font-weight: bold;
        }
        .error {
            margin-top: 16px;
            color: #dc2626;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>동물 투표</h1>
        <form method="post" action="/vote">
            <div class="radio-group">
                <div class="radio-item">
                    <label>
                        <input type="radio" name="animal" value="강아지" required>
                        강아지
                    </label>
                </div>
                <div class="radio-item">
                    <label>
                        <input type="radio" name="animal" value="고양이" required>
                        고양이
                    </label>
                </div>
            </div>

            <div class="buttons">
                <button type="submit">투표</button>
                <button type="submit" formaction="/results" formmethod="get">투표 결과 보기</button>
            </div>
        </form>

        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        {% if results %}
            <div class="result-box">
                <h2>투표 결과</h2>
                <p>강아지: {{ results.get('강아지', 0) }}표</p>
                <p>고양이: {{ results.get('고양이', 0) }}표</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def init_db(max_retries=30, delay=2):
    last_error = None

    for _ in range(max_retries):
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS votes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        animal VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.close()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(delay)

    raise last_error


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, message=None, error=None, results=None)


@app.route("/vote", methods=["POST"])
def vote():
    animal = request.form.get("animal")

    if animal not in ["강아지", "고양이"]:
        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error="잘못된 투표 값입니다.",
            results=None
        )

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO votes (animal) VALUES (%s)",
                (animal,)
            )
        conn.close()

        return render_template_string(
            HTML_TEMPLATE,
            message=f"{animal}에 투표가 저장되었습니다.",
            error=None,
            results=None
        )
    except Exception as exc:
        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error=f"DB 저장 중 오류가 발생했습니다: {exc}",
            results=None
        )


@app.route("/results", methods=["GET"])
def results():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT animal, COUNT(*) AS cnt
                FROM votes
                GROUP BY animal
            """)
            rows = cursor.fetchall()
        conn.close()

        result_map = {row["animal"]: row["cnt"] for row in rows}

        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error=None,
            results=result_map
        )
    except Exception as exc:
        return render_template_string(
            HTML_TEMPLATE,
            message=None,
            error=f"결과 조회 중 오류가 발생했습니다: {exc}",
            results=None
        )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
