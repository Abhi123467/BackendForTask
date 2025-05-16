import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# Define upload folder for images
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = 'taskboard.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the lists table if it doesn't exist
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL
    )''')

    # Create the cards table if it doesn't exist
    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        cover_image_url TEXT,
        card_image_url TEXT,
        FOREIGN KEY (list_id) REFERENCES lists(id)
    )''')

    # Check existing columns in cards table
    cursor.execute("PRAGMA table_info(cards);")
    columns = [column[1] for column in cursor.fetchall()]

    # Add missing columns (safe to rerun)
    if 'cover_image_url' not in columns:
        cursor.execute("ALTER TABLE cards ADD COLUMN cover_image_url TEXT;")
    if 'card_image_url' not in columns:
        cursor.execute("ALTER TABLE cards ADD COLUMN card_image_url TEXT;")
    if 'comment' not in columns:
        cursor.execute("ALTER TABLE cards ADD COLUMN comment TEXT;")
    if 'description' not in columns:
        cursor.execute("ALTER TABLE cards ADD COLUMN description TEXT;")


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
        cursor.execute("""
            SELECT id, text, comment, description, cover_image_url, card_image_url 
            FROM cards WHERE list_id=?
        """, (list_id,))
        cards = cursor.fetchall()
        result.append({
            "id": list_id,
            "title": title,
            "cards": [{
                "id": cid, 
                "text": text, 
                "comment": comment,
                "description": description,
                "cover_image_url": cover_image_url, 
                "card_image_url": card_image_url
            } for cid, text, comment, description, cover_image_url, card_image_url in cards]
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
    comment = data.get('comment', '')
    description = data.get('description', '')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cards (list_id, text, comment, description) VALUES (?, ?, ?, ?)", 
        (list_id, text, comment, description)
    )
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

@app.route("/cards/<int:card_id>", methods=["PUT"])
def update_card(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    text = request.form.get("text")
    comment = request.form.get("comment", "")
    description = request.form.get("description", "")
    remove_cover_image = request.form.get("remove_cover_image") == "true"
    remove_card_image = request.form.get("remove_card_image") == "true"

    # Fetch existing image URLs
    cursor.execute("SELECT cover_image_url, card_image_url FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"message": "Card not found"}), 404

    existing_cover_url, existing_card_url = row
    cover_image_url = existing_cover_url
    card_image_url = existing_card_url

    # Handle cover image upload
    if "cover_image" in request.files:
        cover_image = request.files["cover_image"]
        if cover_image:
            filename = secure_filename(cover_image.filename)
            cover_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            cover_image.save(cover_path)
            cover_image_url = cover_path
    elif remove_cover_image:
        cover_image_url = None
        # Optional: delete the existing file from disk

    # Handle card image upload
    if "card_image" in request.files:
        card_image = request.files["card_image"]
        if card_image:
            filename = secure_filename(card_image.filename)
            card_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            card_image.save(card_path)
            card_image_url = card_path
    elif remove_card_image:
        card_image_url = None
        # Optional: delete the existing file from disk

    # Update the card
    cursor.execute("""
        UPDATE cards
        SET text = ?, comment = ?, description = ?, cover_image_url = ?, card_image_url = ?
        WHERE id = ?
    """, (text, comment, description, cover_image_url, card_image_url, card_id))

    conn.commit()
    conn.close()
    return jsonify({"message": "Card updated successfully"}), 200

@app.route("/cards/<int:card_id>", methods=["GET"])
def get_card(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, text, comment, description, cover_image_url, card_image_url 
        FROM cards WHERE id = ?
    """, (card_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        card_id, text, comment, description, cover_image_url, card_image_url = row
        return jsonify({
            "id": card_id,
            "text": text,
            "comment": comment,
            "description": description,
            "cover_image_url": cover_image_url,
            "card_image_url": card_image_url
        }), 200
    else:
        return jsonify({"message": "Card not found"}), 404

@app.route('/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch existing images for cleanup
    cursor.execute("SELECT cover_image_url, card_image_url FROM cards WHERE id = ?", (card_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"message": "Card not found"}), 404

    cover_image_url, card_image_url = row

    # Delete image files from disk if they exist
    if cover_image_url and os.path.exists(cover_image_url):
        os.remove(cover_image_url)
    if card_image_url and os.path.exists(card_image_url):
        os.remove(card_image_url)

    # Delete the card from the database
    cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Card deleted"}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
