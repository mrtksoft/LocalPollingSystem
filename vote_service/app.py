# vote_service/app.py

from flask import Flask, request, jsonify
import sqlite3
import sys
import os
import json

shared_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shared'))
if shared_dir_path not in sys.path: # duplicates prevention if run multiple times
    sys.path.append(shared_dir_path)
import database

app = Flask(__name__)
PORT = 5002 # Run VoteService on port 5002

## teardown // https://flask.palletsprojects.com/en/stable/appcontext/
@app.teardown_appcontext
def close_db_connection(exception):
    database.close_connection(exception)
    
@app.route('/polls/<string:poll_id>/vote', methods=['POST'])
def cast_vote(poll_id):
    conn = None # for error handling initializez conn to None 
    try:
        data = request.get_json()
        selected_option = data.get('option')

        if not selected_option:
            return jsonify({"error": "Missing 'option' in request body"}), 400

        ##Simple Duplicate vote check using IP address
        # very basic, not bulletproof solution
        #voter_id = request.remote_addr # Getting clients IP address
        vote_id = data.get('userIP')

        conn = database.get_db()
        cursor = conn.cursor()
        
        # Checked here if already has voted in the POLL
        cursor.execute("SELECT 1 FROM voters WHERE poll_id = ? AND voter_id = ?", (poll_id, voter_id))
        already_voted = cursor.fetchone()
        if already_voted:
             print(f"Duplicate vote attempt blocked for {voter_id} on poll {poll_id}")
             return jsonify({"error": "Vote already cast from this IP for this poll."}), 409

        # POLL AND OPTION VALIDITY CHECK
        cursor.execute("SELECT options FROM polls WHERE id = ?", (poll_id,))
        poll_row = cursor.fetchone()
        if not poll_row:
             return jsonify({"error": f"Poll with ID {poll_id} not found"}), 404
        
        valid_options = json.loads(poll_row['options'])
        if selected_option not in valid_options:
             return jsonify({"error": f"Invalid option '{selected_option}' for poll {poll_id}"}), 400

        ##ATOMICALLY increment vote count // More info: https://www.sciencedirect.com/topics/computer-science/atomic-operation
        #Ensuration the row exists with 0 count initially
        cursor.execute("""
            UPDATE votes
            SET count = count + 1
            WHERE poll_id = ? AND option_text = ?
        """, (poll_id, selected_option))
        
        #If the update affected 0 rows
        if cursor.rowcount == 0:
            #This is fallback, ((ideally the row should always exist))
            print(f"Warning: Vote row for {poll_id} / {selected_option} not found, inserting.")
            cursor.execute("INSERT INTO votes (poll_id, option_text, count) VALUES (?, ?, 1)",
                           (poll_id, selected_option))


        # keep a record of who has already voted 
        cursor.execute("INSERT INTO voters (poll_id, voter_id) VALUES (?, ?)", (poll_id, voter_id))
        conn.commit() #commit transaction

        print(f"Vote recorded for option '{selected_option}' in poll '{poll_id}' by {voter_id}")
        return jsonify({"message": f"Vote cast successfully for option '{selected_option}'"}), 200


    #Exception blocks

    except sqlite3.IntegrityError as e: # handleing race condition on inserting voter record
         if conn: conn.rollback()
         print(f"Integrity Error (likely concurrent duplicate vote attempt): {e}")
         return jsonify({"error": "Vote already cast (concurrent attempt)."}), 409
    except sqlite3.Error as e:
        if conn: conn.rollback()
        print(f"Database error: {e}")
        return jsonify({"error": "Database error processing vote"}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error processing vote: {e}")
        return jsonify({"error": "Error processing vote"}), 500

if __name__ == '__main__':
    print(f"Starting Vote Service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True) 
