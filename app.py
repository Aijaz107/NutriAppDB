from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to create the database and table
def create_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT)''')
    conn.commit()
    conn.close()

create_table()

# Error handling decorator
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify(error=str(e)), 500

# Create operation - Add user
@app.route('/add', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return jsonify({'id': user_id, 'name': name, 'email': email}), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

# Read operation - Display all users
@app.route('/')
def get_users():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = [{'id': row[0], 'name': row[1], 'email': row[2]} for row in c.fetchall()]
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify(error=str(e)), 500

# Update operation - Edit user
@app.route('/edit/<int:id>', methods=['PUT'])
def edit_user(id):
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, id))
        conn.commit()
        conn.close()
        return jsonify({'id': id, 'name': name, 'email': email})
    except Exception as e:
        return jsonify(error=str(e)), 500

# Delete operation - Remove user
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
