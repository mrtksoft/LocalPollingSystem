# poll_service/app.py
from flask import Flask, request, jsonify

import sqlite3
import json
import sys
import os

import secrets ## https://docs.python.org/3/library/secrets.html

# Add shared directory
shared_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared'))
if shared_dir_path not in sys.path: # duplicates prevention
    sys.path.append(shared_dir_path)
import database

app = Flask(__name__)
PORT = 5001

#Database is initialized before first request
with app.app_context():
    database.init_db()

#close database connection after each request
@app.teardown_appcontext
def close_db_connection(exception):
    database.close_connection(exception)

@app.route('/polls', methods=['POST'])
def create_poll():
    try:
        data = request.get_json()
        question = data.get('question')
        options = data.get('options') # List of poll strings

        if not question or not options or not isinstance(options, list) or len(options) < 2:
            return jsonify({"error": "Please pass 'question' and 'options' list (min 2)"}), 400

        
        poll_id = secrets.token_urlsafe(12) 
        # Store options as a JSON string
        options_json = json.dumps(options)

        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO polls (id, question, options) VALUES (?, ?, ?)",
                       (poll_id, question, options_json))
        
        # Initialize vote counts to 0 in the votes table
        for option in options:
             cursor.execute("INSERT OR IGNORE INTO votes (poll_id, option_text, count) VALUES (?, ?, 0)",
                           (poll_id, option))
        
        conn.commit()
        return jsonify({'pollId': poll_id, 'message': 'Poll created successfully'}), 201

    except sqlite3.Error as e:
        if conn: conn.rollback() # Rollback on error // https://www.sqlite.org/lang_transaction.html
        print(f"Database error: {e}")
        return jsonify({"error": "Database error creating poll"}), 500
    except Exception as e:
        print(f"Error creating poll: {e}")
        return jsonify({"error": "Error creating poll"}), 500

@app.route('/polls/<string:poll_id>', methods=['GET'])
def get_poll(poll_id):
    try:
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, options FROM polls WHERE id = ?", (poll_id,))
        poll_row = cursor.fetchone()

        if poll_row is None:
            return jsonify({"error": "Poll not found"}), 404

        # Parse JSON string TO LIST [OPTIONS]
        options_list = json.loads(poll_row['options'])

        poll_data = {
            'id': poll_row['id'],
            'question': poll_row['question'],
            'options': options_list
        }
        return jsonify(poll_data), 200

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error fetching poll"}), 500
    except Exception as e:
        print(f"Error fetching poll: {e}")
        return jsonify({"error": "Error fetching poll"}), 500






if __name__ == '__main__':
    print(f"Starting Poll Service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True) # debug=True for development