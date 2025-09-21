# main.py — same as before, just reminding you
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "/var/data/my_private_db.sqlite"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kv_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ 6 GB Database initialized at runtime on Railway volume.")

init_db()

# === API ===

@app.route('/health')
def health():
    return jsonify({"status": "alive", "storage_mounted": "/var/data"}), 200

@app.route('/set', methods=['POST'])
def set_key():
    data = request.json
    key = data.get('key')
    value = data.get('value')
    if not key or not value:
        return jsonify({"error": "key and value required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "key": key}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get/<key>')
def get_key(key):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify({"key": key, "value": row[0]}), 200
        else:
            return jsonify({"error": "not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/size')
def db_size():
    try:
        if os.path.exists(DB_PATH):
            size_bytes = os.path.getsize(DB_PATH)
            size_gb = round(size_bytes / (1024**3), 3)
            free_gb = 6 - size_gb
            return jsonify({
                "db_file": DB_PATH,
                "used_gb": size_gb,
                "free_gb": round(free_gb, 3),
                "total_allocated_gb": 6
            }), 200
        else:
            return jsonify({"error": "DB not created yet"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
