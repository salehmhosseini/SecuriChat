import mysql.connector
from datetime import datetime

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )

def save_message(sender, receiver, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO messages (sender, receiver, content)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (sender, receiver, content))
    conn.commit()
    conn.close()

def get_chat_history(user1, user2):
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
    conn.close()
    
    return [(row['sender'], row['content'], row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")) 
            for row in results]