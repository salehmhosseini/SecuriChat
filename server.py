import socket
import threading
import os
from datetime import datetime
import mysql.connector
import json
from logger import ChatLogger
from crypto_utils import CryptoUtils

# Configuration
SERVER_MEDIA_FOLDER = "server_media"
os.makedirs(SERVER_MEDIA_FOLDER, exist_ok=True)

clients = {}  # username -> socket
logger = ChatLogger()
crypto = CryptoUtils()

def update_last_seen(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = """
        INSERT INTO user_status (username, last_seen)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_seen = VALUES(last_seen)
    """
    cursor.execute(query, (username, now))
    conn.commit()
    conn.close()
    logger.log_connection(username, "Updated last seen")

def save_media_file(file_data, filename):
    filepath = os.path.join(SERVER_MEDIA_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(file_data)
    return filepath

def save_message_to_db(sender, receiver, content, message_type='text', file_path=None, file_size=None):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    query = """
        INSERT INTO messages (sender, receiver, content, message_type, file_path, file_size)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (sender, receiver, content, message_type, file_path, file_size))
    conn.commit()
    conn.close()
    logger.log_message(sender, receiver, message_type, content)

def get_last_seen(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT last_seen FROM user_status WHERE username = %s", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0].strftime("%Y-%m-%d %H:%M:%S") if result and result[0] else "never"

def get_file_metadata(file_name):
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    query = "SELECT file_path, file_size, message_type FROM messages WHERE content = %s"
    cursor.execute(query, (file_name,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None, None)

def handle_client(client_socket):
    try:
        username = client_socket.recv(1024).decode()
        if not username:
            return

        clients[username] = client_socket
        update_last_seen(username)
        logger.log_connection(username, "Connected")

        while True:
            # First receive the header which contains metadata
            header_data = client_socket.recv(1024).decode()
            if not header_data:
                break

            header = json.loads(header_data)
            message_type = header.get('type', 'text')
            
            if message_type == 'text':
                # Regular text message
                content = header.get('content', '')
                if header.get('command') == 'GET_USERS':
                    online_users = set(clients.keys())
                    all_users = set(get_all_known_users())
                    
                    response = {
                        'type': 'user_list',
                        'online': list(online_users),
                        'offline': [{'username': u, 'last_seen': get_last_seen(u)} for u in (all_users - online_users)]
                    }
                    client_socket.send(json.dumps(response).encode())
                    logger.log_connection(username, "Sent user list")
                
                elif header.get('command') == 'CHECK_USER':
                    target = header.get('target')
                    if target in clients:
                        client_socket.send(json.dumps({'status': 'online'}).encode())
                    else:
                        client_socket.send(json.dumps({
                            'status': 'offline',
                            'last_seen': get_last_seen(target)
                        }).encode())
                    logger.log_connection(username, f"Checked status for {target}")
                
                elif header.get('command') == 'GET_FILE':
                    file_name = header.get('file_name')
                    file_path, file_size, file_type = get_file_metadata(file_name)
                    if file_path and os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                        # Encrypt file data
                        encrypted_data = crypto.encrypt(file_data)
                        logger.log_encryption("encrypt_file", f"File: {file_name}")
                        
                        checksum = crypto.calculate_checksum(file_data)
                        logger.log_checksum("calculate", file_data, checksum)
                        
                        response = {
                            'type': 'file',
                            'file_name': file_name,
                            'file_size': len(encrypted_data),
                            'file_type': file_type,
                            'checksum': checksum
                        }
                        client_socket.send(json.dumps(response).encode())
                        client_socket.sendall(encrypted_data)
                        logger.log_file_transfer(username, None, file_name, len(encrypted_data), file_type)
                    else:
                        client_socket.send(json.dumps({
                            'type': 'error',
                            'message': f"File {file_name} not found"
                        }).encode())
                        logger.log_error("FileTransfer", f"File {file_name} not found")
                
                elif header.get('action') == 'send_message':
                    target = header.get('target')
                    checksum = header.get('checksum')
                    
                    # Verify checksum
                    decrypted_content = crypto.decrypt(content.encode())
                    if decrypted_content:
                        calculated_checksum = crypto.calculate_checksum(decrypted_content)
                        logger.log_checksum("verify", decrypted_content, calculated_checksum)
                        
                        if crypto.verify_checksum(decrypted_content, checksum):
                            if target in clients:
                                try:
                                    clients[target].send(json.dumps({
                                        'type': 'message',
                                        'sender': username,
                                        'content': content,
                                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        'checksum': checksum
                                    }).encode())
                                    logger.log_message(username, target, "text", decrypted_content, encrypted=True)
                                except Exception as e:
                                    logger.log_error("SendMessage", f"Failed to send message to {target}: {str(e)}")
                            save_message_to_db(username, target, content)
                        else:
                            logger.log_error("Checksum", "Verification failed for received message")
                    else:
                        logger.log_error("Decryption", "Failed to decrypt received message")
            
            elif message_type in ['image', 'video', 'audio', 'file']:
                # File transfer
                file_size = header['file_size']
                file_name = header['file_name']
                target = header['target']
                checksum = header['checksum']
                
                # Receive file data in chunks
                file_data = b''
                remaining = file_size
                while remaining > 0:
                    chunk = client_socket.recv(min(4096, remaining))
                    if not chunk:
                        break
                    file_data += chunk
                    remaining -= len(chunk)
                
                # Decrypt and verify
                decrypted_data = crypto.decrypt(file_data)
                if decrypted_data:
                    logger.log_encryption("decrypt_file", f"File: {file_name}")
                    calculated_checksum = crypto.calculate_checksum(decrypted_data)
                    logger.log_checksum("verify", decrypted_data, calculated_checksum)
                    
                    if crypto.verify_checksum(decrypted_data, checksum):
                        # Save file to server
                        file_path = save_media_file(decrypted_data, file_name)
                        
                        # Forward to recipient if online
                        if target in clients:
                            try:
                                encrypted_data = crypto.encrypt(decrypted_data)
                                clients[target].send(json.dumps({
                                    'type': 'file_notification',
                                    'sender': username,
                                    'file_name': file_name,
                                    'file_size': len(encrypted_data),
                                    'file_type': message_type,
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'checksum': checksum
                                }).encode())
                                logger.log_file_transfer(username, target, file_name, len(encrypted_data), message_type)
                            except Exception as e:
                                logger.log_error("FileTransfer", f"Failed to send file notification to {target}: {str(e)}")
                        
                        # Save to database
                        save_message_to_db(
                            username, 
                            target, 
                            file_name, 
                            message_type, 
                            file_path, 
                            len(decrypted_data)
                        )
                    else:
                        logger.log_error("Checksum", "Verification failed for received file")
                else:
                    logger.log_error("Decryption", "Failed to decrypt received file")

    except Exception as e:
        logger.log_error("ClientHandler", str(e))
    finally:
        disconnected_user = None
        for name, sock in list(clients.items()):
            if sock == client_socket:
                disconnected_user = name
                break
        
        if disconnected_user:
            update_last_seen(disconnected_user)
            del clients[disconnected_user]
            logger.log_connection(disconnected_user, "Disconnected")
        client_socket.close()

def get_all_known_users():
    conn = mysql.connector.connect(
        host="localhost",
        user="xatovate",
        password="123123",
        database="securichat"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM user_status")
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result] if result else []

def start_server(host='127.0.0.1', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    logger.log_connection("Server", f"Started on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        logger.log_connection("Server", f"New connection from {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_server()