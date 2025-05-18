import socket
import threading
from datetime import datetime
from db import save_message, get_chat_history

def get_user_input(prompt):
    """تابع برای دریافت ورودی کاربر با نمایش prompt"""
    return input(prompt).strip()

def display_chat_history(user1, user2):
    """نمایش تاریخچه چت قبلی"""
    print(f"\n--- Chat history with {user2} ---")
    for sender, msg, time in get_chat_history(user1, user2):
        print(f"[{time}] {sender}: {msg}")
    print("-----------------------------------\n")

def receive_messages(sock, current_user):
    """تابع دریافت پیام‌ها از سرور"""
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                break
                
            # نمایش پیام دریافتی
            print("\n" + message)
            
            # پارس کردن پیام و ذخیره در دیتابیس (فقط اگر پیام از کاربر دیگر است)
            if ": " in message:
                try:
                    # استخراج timestamp, sender و content
                    timestamp_end = message.find("]")
                    timestamp = message[1:timestamp_end]
                    sender = message[timestamp_end+2:message.find(":", timestamp_end)]
                    content = message[message.find(":", timestamp_end)+2:]
                    
                    # ذخیره فقط اگر پیام از کاربر دیگر است
                    if sender.strip() != current_user:
                        save_message(sender.strip(), current_user, content.strip())
                except Exception as e:
                    print(f"[!] Error parsing message: {e}")
                    
        except ConnectionResetError:
            print("[!] Connection lost.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")
            break

def send_messages(sock, sender, receiver):
    """تابع ارسال پیام‌ها به سرور"""
    while True:
        try:
            message = get_user_input("")
            if message.lower() == 'exit':
                break
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_msg = f"[{timestamp}] {sender}: {message}"
            
            sock.send(formatted_msg.encode())
            save_message(sender, receiver, message)  # ذخیره پیام ارسالی
            
        except Exception as e:
            print(f"[!] Failed to send message: {e}")
            break

def start_client(server_ip='127.0.0.1', port=12345):
    """تابع اصلی برای شروع کلاینت"""
    try:
        # دریافت اطلاعات کاربر
        username = get_user_input("Enter your name: ")
        partner = get_user_input("Who do you want to chat with? ")
        
        # نمایش تاریخچه چت
        display_chat_history(username, partner)
        
        # اتصال به سرور
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, port))
        print("[*] Connected to the server. Type 'exit' to quit.")
        
        # شروع thread برای دریافت پیام‌ها
        threading.Thread(
            target=receive_messages,
            args=(client_socket, username),
            daemon=True
        ).start()
        
        # شروع ارسال پیام‌ها
        send_messages(client_socket, username, partner)
        
    except ConnectionRefusedError:
        print("[!] Could not connect to the server.")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client_socket.close()
        print("[*] Disconnected from server.")

if __name__ == "__main__":
    start_client()