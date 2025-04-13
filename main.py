from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from db import init_db, cursor, conn
from marshmallow import ValidationError
from schema import UserSchema, DeeperSchema

app = Flask(__name__)
CORS(app)

user_schema = UserSchema()
deeper_schema = DeeperSchema()

# ==================== User Routes ====================

@app.route("/users", methods=["POST"])
def create_user():
    try:
        data = user_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"message": err.messages}), 400

    cursor.execute("INSERT INTO users (name, phone, extra_info) VALUES (?, ?, ?)",
                (data["name"], data["phone"], data.get("extra_info", "")))
    conn.commit()
    
    return jsonify({"message": "User created"}), 201
    
@app.route("/users", methods=["GET"])
def read_users():
    users = cursor.execute("SELECT * FROM users").fetchall()
    return jsonify([dict(u) for u in users]), 200

@app.route("/users/<id>", methods=["GET"])
def read_user_by_id(id):
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404
    user_data = dict(user)
    deepers = cursor.execute("SELECT * FROM deepers WHERE user_id = ?", (id,)).fetchall()
    user_data["deepers"] = [dict(deeper) for deeper in deepers]
    return jsonify(user_data), 200
    
@app.route("/users/<id>", methods=["PATCH"])
def update_user(id):
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    try:
        data = user_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({"message": err.messages}), 400

    cursor.execute("UPDATE users SET name = ?, phone = ?, extra_info = ? WHERE id = ?",
        (data["name"], data["phone"], data.get("extra_info", ""), id))
    conn.commit()

    return jsonify({"message": "User updated"}), 200
    
@app.route("/users/<id>", methods=["DELETE"])
def delete_user(id):
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404

    cursor.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()

    return jsonify({"message": "User deleted"}), 204

# ==================== Deeper Routes ====================

@app.route("/deepers", methods=["POST"])
def create_deeper():
    try:
        data = deeper_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"message": err.messages}), 400

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (data["user_id"],)).fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    cursor.execute("INSERT INTO deepers (user_id, name, phone, extra_info, memo) VALUES (?, ?, ?, ?, ?)",
                (data["user_id"], data["name"], data["phone"], data.get("extra_info", ""), data.get("memo", "")))
    conn.commit()
    
    return jsonify({"message": "Deeper created"}), 201

@app.route("/deepers", methods=["GET"])
def read_deepers():
    user_id = request.args.get("user_id")
    if user_id:
        deepers = cursor.execute("SELECT * FROM deepers WHERE user_id = ?", (user_id,)).fetchall()
    else:
        deepers = cursor.execute("SELECT * FROM deepers").fetchall()
    return jsonify([dict(d) for d in deepers]), 200

@app.route("/deepers/<id>", methods=["GET"])
def read_deeper_by_id(id):
    deeper = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
    if not deeper:
        return jsonify({"message": "Deeper not found"}), 404
    return jsonify(dict(deeper)), 200

@app.route("/deepers/<id>", methods=["PATCH"])
def update_deeper(id):
    deepers = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
    if not deepers:
        return jsonify({"message": "Deeper not found"}), 404
    
    try:
        data = deeper_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({"message": err.messages}), 400

    cursor.execute("UPDATE deepers SET name = ?, phone = ?, extra_info = ?, memo = ? WHERE id = ?",
        (data["name"], data["phone"], data.get("extra_info", ""), data.get("memo", ""), id))
    conn.commit()

    return jsonify({"message": "Deeper updated"}), 200

@app.route("/deepers/<id>", methods=["DELETE"])
def delete_deeper(id):
    deepers = cursor.execute("SELECT * FROM deepers WHERE id = ?", (id,)).fetchone()
    if not deepers:
        return jsonify({"message": "Deeper not found"}), 404

    cursor.execute("DELETE FROM deepers WHERE id = ?", (id,))
    conn.commit()

    return jsonify({"message": "Deeper deleted"}), 204

# ==================== Run App ====================

if __name__ == "__main__":
    load_dotenv()
    init_db()
    app.run(host="127.0.0.1", port=8080, debug=True)