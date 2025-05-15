from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

DB_PATH = 'taskboard.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (list_id) REFERENCES lists(id)
    )''')
    conn.commit()
    conn.close()

@app.route('/lists', methods=['GET'])
def get_lists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lists")
    lists = cursor.fetchall()
    result = []
    for list_id, title in lists:
        cursor.execute("SELECT id, text FROM cards WHERE list_id=?", (list_id,))
        cards = cursor.fetchall()
        result.append({
            "id": list_id,
            "title": title,
            "cards": [{"id": cid, "text": text} for cid, text in cards]
        })
    conn.close()
    return jsonify(result)

@app.route('/lists', methods=['POST'])
def add_list():
    data = request.get_json()
    title = data.get('title')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lists (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()
    return jsonify({"message": "List added"}), 201

@app.route('/cards', methods=['POST'])
def add_card():
    data = request.get_json()
    list_id = data.get('list_id')
    text = data.get('text')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cards (list_id, text) VALUES (?, ?)", (list_id, text))
    conn.commit()
    conn.close()
    return jsonify({"message": "Card added"}), 201

@app.route('/lists/<int:list_id>', methods=['PUT'])
def update_list(list_id):
    data = request.get_json()
    title = data.get('title')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE lists SET title = ? WHERE id = ?", (title, list_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "List updated"}), 200

@app.route('/lists/<int:list_id>', methods=['DELETE'])
def delete_list(list_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE list_id = ?", (list_id,))
    cursor.execute("DELETE FROM lists WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "List deleted"}), 200
@app.route('/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    data = request.get_json()
    text = data.get('text')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE cards SET text = ? WHERE id = ?", (text, card_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Card updated"}), 200

@app.route('/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Card deleted"}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)