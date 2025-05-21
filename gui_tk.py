import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import socket
from datetime import datetime
from db import save_message, get_chat_history
import webbrowser  # For hyperlink support

class SecuriChatGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("SecuriChat - Secure Messaging")
        self.master.geometry("800x600")
        self.master.minsize(700, 500)
        self.master.configure(bg="#2c3e50")
        
        # Custom style configuration
        self.setup_styles()
        
        self.username = None
        self.partner = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Add app header
        self.header = ttk.Label(
            self.master, 
            text="SecuriChat", 
            style='Header.TLabel',
            cursor="hand2"
        )
        self.header.pack(fill=tk.X, pady=(10, 20))
        self.header.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/your-repo"))
        
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
        
        # Scrollbar styles
        style.configure('Vertical.TScrollbar',
                       background='#34495e',
                       troughcolor='#2c3e50',
                       bordercolor='#2c3e50',
                       arrowcolor='white')
        
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
            return

        try:
            self.client_socket.connect(('127.0.0.1', 12345))
            self.client_socket.send(self.username.encode())
            self.select_user_screen()
        except Exception as e:
            messagebox.showerror("Connection Error", 
                                f"Failed to connect to server:\n{str(e)}", 
                                parent=self.master)

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
            self.client_socket.send(b"GET_USERS")
            users = self.client_socket.recv(4096).decode()
            
            for line in users.splitlines():
                if line.strip() and not line.startswith("==="):
                    parts = line.split("-")
                    username = parts[0].strip()
                    status = parts[1].strip() if len(parts) > 1 else ""
                    
                    if "Online" in status:
                        self.user_list.insert(tk.END, f"🟢 {username}")
                    else:
                        self.user_list.insert(tk.END, f"⚪ {username}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get user list:\n{str(e)}", parent=self.master)

    def refresh_user_list(self):
        """Refresh the list of available users"""
        self.populate_user_list()
        messagebox.showinfo("Info", "User list refreshed", parent=self.master)

    def disconnect(self):
        """Disconnect from the server"""
        try:
            self.client_socket.close()
        except:
            pass
        self.login_screen()

    def start_chat_with_user(self):
        """Start chat with selected user"""
        selected = self.user_list.get(tk.ACTIVE)
        if not selected:
            messagebox.showinfo("Info", "Please select a user to chat with.", parent=self.master)
            return

        # Extract username (remove status indicator)
        self.partner = selected[2:].strip()
        
        self.client_socket.send(f"CHECK_USER:{self.partner}".encode())
        status = self.client_socket.recv(1024).decode()

        if status.startswith("OFFLINE"):
            last_seen = status.split(":", 1)[1]
            messagebox.showinfo("User Offline", 
                              f"User '{self.partner}' is offline. Last seen: {last_seen}", 
                              parent=self.master)
            return

        self.chat_screen()

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
        
        # Message entry
        entry_frame = ttk.Frame(main_frame)
        entry_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_entry = ttk.Entry(
            entry_frame,
            font=('Helvetica', 12)
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        self.message_entry.bind("<Return>", self.send_message_event)
        self.message_entry.focus()
        
        ttk.Button(entry_frame, 
                  text="Send", 
                  style='Success.TButton',
                  command=self.send_message).pack(side=tk.RIGHT, ipady=3)
        
        # Load chat history
        self.load_chat_history()
        
        # Start message receiver thread
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def load_chat_history(self):
        """Load chat history from database"""
        try:
            history = get_chat_history(self.username, self.partner)
            for sender, msg, time_ in history:
                self.append_message(f"[{time_}] {sender}: {msg}")
        except Exception as e:
            self.append_message("[System] Failed to load chat history")

    def send_message_event(self, event):
        """Handle Enter key press for sending messages"""
        self.send_message()

    def send_message(self):
        """Send a message to the current chat partner"""
        msg = self.message_entry.get().strip()
        if not msg:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {self.username}: {msg}"
        try:
            self.client_socket.send(f"TO:{self.partner}:{formatted}".encode())
            save_message(self.username, self.partner, msg)
            self.append_message(formatted)
            self.message_entry.delete(0, tk.END)
        except Exception as e:
            self.append_message(f"[System] Error sending message: {str(e)}")

    def receive_messages(self):
        """Receive messages from the server"""
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.append_message(message)
                    if ": " in message:
                        parts = message.split(": ", 1)
                        if len(parts) == 2:
                            sender, content = parts
                            save_message(sender.strip("[] "), self.username, content.strip())
            except:
                self.append_message("[System] Disconnected from server")
                break

    def append_message(self, message):
        """Append a message to the chat display"""
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, message + '\n')
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