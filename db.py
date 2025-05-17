import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )

def save_message(sender, receiver, content):
    conn = connect_db()
    cursor = conn.cursor()
    query = "INSERT INTO messages (sender, receiver, content) VALUES (%s, %s, %s)"
    cursor.execute(query, (sender, receiver, content))
    conn.commit()
    conn.close()

def get_chat_history(user1, user2):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
        SELECT sender, content, timestamp FROM messages
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s)
        ORDER BY timestamp
    """
    cursor.execute(query, (user1, user2, user2, user1))
    messages = cursor.fetchall()
    conn.close()
    return messages
