import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont
import threading
import socket
import os
import json
from datetime import datetime
from PIL import Image, ImageTk
import io
import base64
from db import save_message, get_chat_history
from logger import ChatLogger
from crypto_utils import CryptoUtils

class SecuriChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("SecuriChat - Secure Messaging")
        self.master.geometry("900x700")
        self.master.minsize(800, 600)
        self.master.configure(bg="#2c3e50")
        
        self.logger = ChatLogger()
        self.crypto = CryptoUtils()
        
        # Custom style configuration
        self.setup_styles()
        
        self.username = None
        self.partner = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.media_folder = "client_media"
        os.makedirs(self.media_folder, exist_ok=True)
        
        # Add app header
        self.header = ttk.Label(
            self.master, 
            text="SecuriChat", 
            style='Header.TLabel',
            cursor="hand2"
        )
        self.header.pack(fill=tk.X, pady=(10, 20))
        
        self.login_screen()

    def setup_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Background colors
        style.configure('.', background='#2c3e50', foreground='white')
        style.configure('TFrame', background='#2c3e50')
        
        # Header style
        style.configure('Header.TLabel', 
                       font=('Helvetica', 24, 'bold'), 
                       foreground='#3498db',
                       background='#2c3e50',
                       anchor='center')
        
        # Button styles
        style.configure('Primary.TButton', 
                       font=('Helvetica', 12),
                       foreground='white',
                       background='#3498db',
                       bordercolor='#3498db',
                       borderwidth=1,
                       focuscolor='#3498db')
        style.map('Primary.TButton',
                 background=[('active', '#2980b9')])
        
        style.configure('Success.TButton', 
                       font=('Helvetica', 12),
                       foreground='white',
                       background='#2ecc71',
                       bordercolor='#2ecc71')
        style.map('Success.TButton',
                 background=[('active', '#27ae60')])
        
        # Entry styles
        style.configure('TEntry',
                       fieldbackground='#ecf0f1',
                       foreground='#2c3e50',
                       insertcolor='#2c3e50',
                       padding=5)
        
        # Listbox styles
        style.configure('TListbox',
                       background='#ecf0f1',
                       foreground='#2c3e50',
                       selectbackground='#3498db',
                       selectforeground='white',
                       font=('Helvetica', 11))
        
        # Chat display styles
        style.configure('Chat.TFrame',
                       background='white',
                       borderwidth=2,
                       relief='sunken')

    def login_screen(self):
        """Display the login screen"""
        self.clear_window()
        
        login_frame = ttk.Frame(self.master, padding=20)
        login_frame.pack(expand=True)
        
        ttk.Label(login_frame, 
                 text="Welcome to SecuriChat", 
                 font=('Helvetica', 16),
                 anchor='center').pack(pady=(0, 20))
        
        ttk.Label(login_frame, 
                 text="Enter your username:", 
                 font=('Helvetica', 12)).pack(pady=5)
        
        self.username_entry = ttk.Entry(login_frame, 
                                      font=('Helvetica', 12),
                                      width=30,
                                      style='TEntry')
        self.username_entry.pack(pady=5, ipady=5)
        self.username_entry.focus()
        
        ttk.Button(login_frame, 
                  text="Connect", 
                  style='Success.TButton',
                  command=self.connect_to_server).pack(pady=15, ipady=5)
        
        # Footer
        footer = ttk.Frame(self.master)
        footer.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(footer, 
                 text="© 2023 SecuriChat | Secure Messaging", 
                 font=('Helvetica', 8),
                 anchor='center').pack()

    def connect_to_server(self):
        """Connect to the chat server"""
        self.username = self.username_entry.get().strip()
        if not self.username:
            messagebox.showerror("Error", "Username cannot be empty", parent=self.master)
            self.logger.log_error("Connection", "Empty username attempted")
            return

        try:
            self.client_socket.connect(('127.0.0.1', 12345))
            # Send username as first message
            self.client_socket.send(self.username.encode())
            self.logger.log_connection(self.username, "Connected")
            self.select_user_screen()
            # Start message receiver thread
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", 
                                f"Failed to connect to server:\n{str(e)}", 
                                parent=self.master)
            self.logger.log_error("Connection", str(e))

    def select_user_screen(self):
        """Display the user selection screen"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, 
                 text=f"Connected as: {self.username}", 
                 font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, 
                  text="Refresh", 
                  style='Primary.TButton',
                  command=self.refresh_user_list).pack(side=tk.RIGHT)
        
        # User list
        ttk.Label(main_frame, 
                 text="Select a user to chat with:", 
                 font=('Helvetica', 12)).pack(anchor='w')
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.user_list = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Helvetica', 11),
            selectbackground='#3498db',
            selectforeground='white',
            activestyle='none',
            borderwidth=0,
            highlightthickness=0
        )
        self.user_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.user_list.yview)
        
        # Populate user list
        self.populate_user_list()
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, 
                  text="Start Chat", 
                  style='Success.TButton',
                  command=self.start_chat_with_user).pack(side=tk.RIGHT, ipady=3)
        
        ttk.Button(button_frame, 
                  text="Disconnect", 
                  style='Primary.TButton',
                  command=self.disconnect).pack(side=tk.LEFT, ipady=3)

    def populate_user_list(self):
        """Populate the user list from server"""
        self.user_list.delete(0, tk.END)
        try:
            # Send request for user list
            header = {
                'command': 'GET_USERS',
                'type': 'text'
            }
            self.client_socket.send(json.dumps(header).encode())
            self.logger.log_connection(self.username, "Requested user list")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get user list:\n{str(e)}", parent=self.master)
            self.logger.log_error("UserList", str(e))

    def refresh_user_list(self):
        """Refresh the list of available users"""
        self.populate_user_list()
        messagebox.showinfo("Info", "User list refreshed", parent=self.master)
        self.logger.log_connection(self.username, "Refreshed user list")

    def disconnect(self):
        """Disconnect from the server"""
        try:
            self.client_socket.close()
            self.logger.log_connection(self.username, "Disconnected")
        except Exception as e:
            self.logger.log_error("Disconnect", str(e))
        self.login_screen()

    def start_chat_with_user(self):
        """Start chat with selected user"""
        selected = self.user_list.get(tk.ACTIVE)
        if not selected:
            messagebox.showinfo("Info", "Please select a user to chat with.", parent=self.master)
            self.logger.log_error("Chat", "No user selected")
            return

        # Extract username (remove status indicator)
        self.partner = selected[2:].strip().split(' (')[0]
        
        # Check if user is online
        header = {
            'command': 'CHECK_USER',
            'target': self.partner,
            'type': 'text'
        }
        self.client_socket.send(json.dumps(header).encode())
        self.logger.log_connection(self.username, f"Checking status for {self.partner}")

    def chat_screen(self):
        """Display the chat screen"""
        self.clear_window()
        
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, 
                 text=f"Chatting with: {self.partner}", 
                 font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, 
                  text="Back", 
                  style='Primary.TButton',
                  command=self.select_user_screen).pack(side=tk.RIGHT)
        
        # Chat display
        chat_frame = ttk.Frame(main_frame, style='Chat.TFrame')
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Helvetica', 11),
            padx=10,
            pady=10,
            state='disabled',
            bg='white',
            fg='#2c3e50',
            insertbackground='#2c3e50',
            selectbackground='#3498db'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Message input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Attachment button
        attach_btn = ttk.Button(
            input_frame,
            text="📎",
            style='Primary.TButton',
            command=self.attach_file
        )
        attach_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.message_entry = ttk.Entry(
            input_frame,
            font=('Helvetica', 12)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.message_entry.bind("<Return>", self.send_message_event)
        self.message_entry.focus()
        
        send_btn = ttk.Button(
            input_frame,
            text="Send",
            style='Success.TButton',
            command=self.send_message
        )
        send_btn.pack(side=tk.RIGHT, ipady=3)
        
        # Load chat history
        self.load_chat_history()

    def attach_file(self):
        """Open file dialog to attach a file"""
        filepath = filedialog.askopenfilename(
            title="Select file to send",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.gif"),
                ("Videos", "*.mp4 *.avi *.mov"),
                ("Audio", "*.mp3 *.wav"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            try:
                # Read file data
                with open(filepath, 'rb') as f:
                    file_data = f.read()
                
                # Encrypt file data
                encrypted_data = self.crypto.encrypt(file_data)
                self.logger.log_encryption("encrypt_file", f"File: {os.path.basename(filepath)}")
                
                # Calculate checksum
                checksum = self.crypto.calculate_checksum(file_data)
                self.logger.log_checksum("calculate", file_data, checksum)
                
                # Determine file type
                filename = os.path.basename(filepath)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ('.jpg', '.jpeg', '.png', '.gif'):
                    file_type = 'image'
                elif ext in ('.mp4', '.avi', '.mov'):
                    file_type = 'video'
                elif ext in ('.mp3', '.wav'):
                    file_type = 'audio'
                else:
                    file_type = 'file'
                
                # Send file metadata first
                header = {
                    'type': file_type,
                    'target': self.partner,
                    'file_name': filename,
                    'file_size': len(encrypted_data),
                    'action': 'send_file',
                    'checksum': checksum
                }
                self.client_socket.send(json.dumps(header).encode())
                
                # Then send the encrypted file data
                self.client_socket.sendall(encrypted_data)
                
                # Show in chat
                self.append_message(f"[You sent a file: {filename}]", is_me=True, file_name=filename)
                self.logger.log_file_transfer(self.username, self.partner, filename, len(encrypted_data), file_type)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send file: {str(e)}", parent=self.master)
                self.logger.log_error("FileTransfer", str(e))

    def load_chat_history(self):
        """Load chat history from database"""
        try:
            history = get_chat_history(self.username, self.partner)
            for msg in history:
                sender, content, time_, msg_type, file_path = msg
                if msg_type == 'text':
                    try:
                        # Attempt to decrypt message
                        decrypted_content = self.crypto.decrypt(content.encode())
                        if decrypted_content:
                            self.append_message(f"[{time_}] {sender}: {decrypted_content}")
                        else:
                            self.append_message(f"[{time_}] {sender}: [Encrypted message - decryption failed]")
                    except:
                        self.append_message(f"[{time_}] {sender}: {content}")
                else:
                    self.append_message(f"[{time_}] {sender}: Sent a {msg_type} - {content}", file_name=content)
            self.logger.log_connection(self.username, f"Loaded chat history with {self.partner}")
        except Exception as e:
            self.append_message(f"[System] Failed to load chat history: {str(e)}")
            self.logger.log_error("ChatHistory", str(e))

    def send_message_event(self, event):
        """Handle Enter key press for sending messages"""
        self.send_message()

    def send_message(self):
        """Send a message to the current chat partner"""
        msg = self.message_entry.get().strip()
        if not msg:
            return

        try:
            # Encrypt message
            encrypted_msg = self.crypto.encrypt(msg)
            checksum = self.crypto.calculate_checksum(msg)
            
            self.logger.log_encryption("encrypt_message", f"Message length: {len(msg)}")
            self.logger.log_checksum("calculate", msg, checksum)
            
            header = {
                'action': 'send_message',
                'target': self.partner,
                'type': 'text',
                'content': encrypted_msg.decode(),
                'checksum': checksum
            }
            self.client_socket.send(json.dumps(header).encode())
            
            # Save to local chat
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.append_message(f"[{timestamp}] {self.username}: {msg}", is_me=True)
            self.message_entry.delete(0, tk.END)
            
            # Save to database (encrypted)
            save_message(self.username, self.partner, encrypted_msg.decode())
            self.logger.log_message(self.username, self.partner, "text", msg, encrypted=True)
            
        except Exception as e:
            self.append_message(f"[System] Error sending message: {str(e)}")
            self.logger.log_error("SendMessage", str(e))

    def request_file_download(self, file_name):
        """Request file download from server"""
        try:
            header = {
                'command': 'GET_FILE',
                'type': 'text',
                'file_name': file_name
            }
            self.client_socket.send(json.dumps(header).encode())
            self.logger.log_connection(self.username, f"Requested file download: {file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to request file: {str(e)}", parent=self.master)
            self.logger.log_error("FileDownload", str(e))

    def save_received_file(self, file_name, file_data, file_type, checksum):
        """Save received file to client_media folder"""
        try:
            # Verify checksum
            calculated_checksum = self.crypto.calculate_checksum(file_data)
            self.logger.log_checksum("verify", file_data, calculated_checksum)
            
            if not self.crypto.verify_checksum(file_data, checksum):
                raise ValueError("Checksum verification failed")
            
            # Decrypt file data
            decrypted_data = self.crypto.decrypt(file_data)
            if decrypted_data is None:
                raise ValueError("File decryption failed")
                
            self.logger.log_encryption("decrypt_file", f"File: {file_name}")
            
            filepath = os.path.join(self.media_folder, file_name)
            with open(filepath, 'wb') as f:
                f.write(decrypted_data.encode() if isinstance(decrypted_data, str) else decrypted_data)
            messagebox.showinfo("Success", f"File saved to {filepath}", parent=self.master)
            self.append_message(f"[System] Downloaded file: {file_name}")
            self.logger.log_file_transfer(self.partner, self.username, file_name, len(file_data), file_type)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}", parent=self.master)
            self.logger.log_error("SaveFile", str(e))

    def receive_messages(self):
        """Receive messages from the server"""
        while True:
            try:
                # First receive the header/metadata
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                
                message = json.loads(data)
                
                if message.get('type') == 'user_list':
                    # Update user list
                    self.user_list.delete(0, tk.END)
                    for user in message.get('online', []):
                        self.user_list.insert(tk.END, f"🟢 {user}")
                    for user in message.get('offline', []):
                        self.user_list.insert(tk.END, f"⚪ {user['username']} (Last seen: {user['last_seen']})")
                    self.logger.log_connection(self.username, "Received user list")
                
                elif message.get('type') == 'status':
                    # User status update
                    if message.get('status') == 'online':
                        self.append_message(f"[System] {message['username']} is now online")
                    else:
                        self.append_message(f"[System] {message['username']} is now offline")
                    self.logger.log_connection(message['username'], message['status'])
                
                elif message.get('type') == 'message':
                    # Regular text message
                    content = message.get('content')
                    checksum = message.get('checksum')
                    
                    # Decrypt message
                    decrypted_content = self.crypto.decrypt(content.encode())
                    self.logger.log_encryption("decrypt_message", f"Message length: {len(content)}")
                    
                    if decrypted_content:
                        # Verify checksum
                        calculated_checksum = self.crypto.calculate_checksum(decrypted_content)
                        self.logger.log_checksum("verify", decrypted_content, calculated_checksum)
                        
                        if self.crypto.verify_checksum(decrypted_content, checksum):
                            self.append_message(f"[{message.get('timestamp')}] {message.get('sender')}: {decrypted_content}")
                            self.logger.log_message(message.get('sender'), self.username, "text", decrypted_content, encrypted=True)
                        else:
                            self.append_message(f"[{message.get('timestamp')}] {message.get('sender')}: [Checksum verification failed]")
                            self.logger.log_error("Checksum", "Verification failed for received message")
                    else:
                        self.append_message(f"[{message.get('timestamp')}] {message.get('sender')}: [Decryption failed]")
                        self.logger.log_error("Decryption", "Failed to decrypt received message")
                
                elif message.get('type') == 'file_notification':
                    # File received notification
                    self.append_message(
                        f"[{message.get('timestamp')}] {message.get('sender')} sent a {message.get('file_type')}: {message.get('file_name')}",
                        file_name=message.get('file_name')
                    )
                    self.logger.log_file_transfer(message.get('sender'), self.username, 
                                               message.get('file_name'), 
                                               message.get('file_size'), 
                                               message.get('file_type'))
                
                elif message.get('type') == 'file':
                    # Receiving file data
                    file_size = message.get('file_size')
                    file_name = message.get('file_name')
                    file_type = message.get('file_type')
                    checksum = message.get('checksum')
                    file_data = b''
                    remaining = file_size
                    while remaining > 0:
                        chunk = self.client_socket.recv(min(4096, remaining))
                        if not chunk:
                            break
                        file_data += chunk
                        remaining -= len(chunk)
                    self.save_received_file(file_name, file_data, file_type, checksum)
                
                elif message.get('type') == 'error':
                    self.append_message(f"[System] Error: {message.get('message')}")
                    self.logger.log_error("Server", message.get('message'))
                
                elif message.get('status') == 'online':
                    # Response to CHECK_USER
                    self.chat_screen()
                
                elif message.get('status') == 'offline':
                    # Response to CHECK_USER
                    messagebox.showinfo(
                        "User Offline", 
                        f"User '{self.partner}' is offline. Last seen: {message.get('last_seen')}", 
                        parent=self.master
                    )
                    self.logger.log_connection(self.partner, "Offline")
                    
            except json.JSONDecodeError:
                self.logger.log_error("JSON", "Invalid JSON received")
                continue
            except Exception as e:
                self.append_message(f"[System] Disconnected from server: {str(e)}")
                self.logger.log_error("ReceiveMessage", str(e))
                break

    def append_message(self, message, is_me=False, file_name=None):
        """Append a message to the chat display"""
        self.chat_display.configure(state='normal')
        
        # Configure tag for "me" vs "them"
        tag = "me" if is_me else "them"
        self.chat_display.tag_config(tag, foreground="#3498db" if is_me else "#2c3e50")
        
        self.chat_display.insert(tk.END, message, (tag,))
        
        # Add download button for file messages
        if file_name:
            download_button = ttk.Button(
                self.chat_display,
                text="Download",
                style='Primary.TButton',
                command=lambda: self.request_file_download(file_name)
            )
            self.chat_display.window_create(tk.END, window=download_button)
        
        self.chat_display.insert(tk.END, '\n')
        self.chat_display.configure(state='disabled')
        self.chat_display.yview(tk.END)

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.master.winfo_children():
            if widget not in [self.header]:
                widget.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = SecuriChatGUI(root)
    root.mainloop()