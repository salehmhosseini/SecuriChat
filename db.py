import mysql.connector
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )

def save_message(sender, receiver, content, message_type='text', file_path=None, file_size=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO messages (sender, receiver, content, message_type, file_path, file_size)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (sender, receiver, content, message_type, file_path, file_size))
    conn.commit()
    conn.close()

def get_chat_history(user1, user2):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT sender, content, timestamp, message_type, file_path 
        FROM messages 
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY timestamp
    """
    cursor.execute(query, (user1, user2, user2, user1))
    results = cursor.fetchall()
    conn.close()
    
    return [(row['sender'], row['content'], row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"), 
             row['message_type'], row['file_path']) 
            for row in results]