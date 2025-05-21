import mysql.connector
from datetime import datetime

def get_db_connection():
    """Create and return a new database connection"""
    return mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )

def save_message(sender, receiver, content):
    """Save a message to the database"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO messages (sender, receiver, content)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (sender, receiver, content))
        conn.commit()
    except Exception as e:
        print(f"Error saving message: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_chat_history(user1, user2):
    """Retrieve chat history between two users"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT sender, content, timestamp 
            FROM messages 
            WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
            ORDER BY timestamp
        """
        cursor.execute(query, (user1, user2, user2, user1))
        results = cursor.fetchall()
        
        chat_history = []
        for row in results:
            chat_history.append((
                row['sender'],
                row['content'],
                row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            ))
        return chat_history
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()