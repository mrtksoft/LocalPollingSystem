# result_service/app.py
from flask import Flask, request, jsonify
import sqlite3
import sys
import os
import json

shared_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared'))
if shared_dir_path not in sys.path: # Avoid adding duplicates if run multiple times
    sys.path.append(shared_dir_path)
import database

app = Flask(__name__)
PORT = 5003 # Run ResultService on port 5003


## teardown // https://flask.palletsprojects.com/en/stable/appcontext/
@app.teardown_appcontext
def close_db_connection(exception):
    database.close_connection(exception)

@app.route('/polls/<string:poll_id>/results', methods=['GET'])
def get_results(poll_id):
    try:
        conn = database.get_db()
        cursor = conn.cursor()
        # gets question and options
        cursor.execute("SELECT question, options FROM polls WHERE id = ?", (poll_id,))
        poll_row = cursor.fetchone()

        if poll_row is None:
            return jsonify({"error": "Poll not found"}), 404
        question = poll_row['question']
        options_list = json.loads(poll_row['options']) # takes a string containing JSON data and stores it to a list

        # amoount of votes for poll counted by rows
        cursor.execute("SELECT option_text, count FROM votes WHERE poll_id = ?", (poll_id,))
        vote_rows = cursor.fetchall()

        #formatting results
        final_results = {option: 0 for option in options_list} # Initialize options = 0 
        total_votes = 0
        for row in vote_rows:
            if row['option_text'] in final_results: # inclusion of valsid opitons
                final_results[row['option_text']] = row['count']
                total_votes += row['count']

        response_data = {
            'pollId': poll_id,
            'question': question,
            'results': final_results,
            'totalVotes': total_votes
        }


        # -**- Comment for improvement caching could be implemented here for next version. (e.g., Flask-Caching)


        return jsonify(response_data), 200


##Exceotuion blocks 
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error fetching results"}), 500

    except Exception as e:
        print(f"Error fetching results: {e}")
        return jsonify({"error": "Error fetching results"}), 500

if __name__ == '__main__':
    print(f"Starting Result Service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)