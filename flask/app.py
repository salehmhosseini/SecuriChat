from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
from db import save_message, get_chat_history
import mysql.connector
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-very-secret-key-123'  # Change this in production!
socketio = SocketIO(app)

# Track connected users in memory
connected_users = {}

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'xatovate',
    'password': '123123',
    'database': 'securichat'
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return redirect(url_for('chat'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if username:
            session['username'] = username
            update_last_seen(username)
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        update_last_seen(session['username'])
        session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    partner = request.args.get('partner', '')
    chat_history = []
    if partner:
        try:
            chat_history = get_chat_history(session['username'], partner)
        except Exception as e:
            print(f"Error loading chat history: {e}")
    return render_template('chat.html',
                         username=session['username'],
                         partner=partner,
                         chat_history=chat_history)

@app.route('/users')
@login_required
def users():
    # Get all registered users from database
    all_users = get_all_users()
    
    # Mark which ones are currently connected
    users_with_status = []
    for user in all_users:
        users_with_status.append({
            'username': user,
            'status': 'online' if user in connected_users else 'offline',
            'last_seen': get_last_seen(user) if user not in connected_users else 'Now'
        })
    
    return render_template('users.html',
                         username=session['username'],
                         users=users_with_status)

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    if 'username' in session:
        username = session['username']
        connected_users[username] = request.sid
        join_room(username)
        update_last_seen(username)
        
        # Notify all clients about this user coming online
        emit('user_status_change', {
            'username': username,
            'status': 'online',
            'last_seen': 'Now'
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' in session:
        username = session['username']
        if username in connected_users:
            del connected_users[username]
            last_seen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_last_seen(username)
            
            # Notify all clients about this user going offline
            emit('user_status_change', {
                'username': username,
                'status': 'offline',
                'last_seen': last_seen
            }, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    if 'username' not in session:
        return
    
    sender = session['username']
    receiver = data.get('receiver', '')
    message = data.get('message', '').strip()
    
    if not receiver or not message:
        return
    
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_message(sender, receiver, message)
        
        emit('receive_message', {
            'sender': sender,
            'message': message,
            'timestamp': timestamp
        }, room=receiver)
        
        emit('receive_message', {
            'sender': sender,
            'message': message,
            'timestamp': timestamp
        }, room=sender)
    except Exception as e:
        print(f"Error sending message: {e}")

# Database helper functions
def update_last_seen(username):
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO user_status (username, last_seen)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE last_seen = VALUES(last_seen)
        """
        cursor.execute(query, (username, now))
        conn.commit()
    except Exception as e:
        print(f"Error updating last seen: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_last_seen(username):
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT last_seen FROM user_status 
            WHERE username = %s
        """, (username,))
        result = cursor.fetchone()
        if result:
            return result[0].strftime("%Y-%m-%d %H:%M:%S")
        return "Never"
    except Exception as e:
        print(f"Error getting last seen: {e}")
        return "Unknown"
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_all_users():
    """Get all registered users from database"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM user_status ORDER BY username")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')