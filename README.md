# SecuriChat

SecuriChat is a secure messaging application built with Python, Tkinter, and socket programming. It allows users to connect to a server, select a chat partner, send encrypted text messages and files, and view chat history. The application includes robust logging for all events and implements AES encryption with CRC32 checksums for error detection.

## Features

- **User Interface**: A modern Tkinter-based GUI with a dark theme, supporting login, user selection, and chat screens.
- **Real-time Messaging**: Send and receive text messages instantly with a selected user.
- **File Transfer**: Share images, videos, audio files, and other file types securely.
- **Encryption**: Messages and files are encrypted using AES (via Fernet) to ensure secure communication.
- **Error Detection**: CRC32 checksums verify the integrity of messages and files.
- **Logging**: Comprehensive logging of all events (connections, messages, file transfers, encryption, errors) to timestamped log files.
- **Chat History**: Stores messages and file metadata in a MySQL database for persistent history.
- **User Status**: Displays online/offline status and last seen timestamps for users.

## Requirements

- Python 3.8+
- Required Python packages:
  - `tkinter` (usually included with Python)
  - `mysql-connector-python`
  - `cryptography`
  - `Pillow` (for image handling in the GUI)
- MySQL server (e.g., MySQL Community Server)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/salehmhosseini/SecuriChat.git
   cd securichat
   ```

2. **Install Dependencies**:
   Install the required Python packages:
   ```bash
   pip install mysql-connector-python cryptography Pillow
   ```

3. **Set Up MySQL Database**:
   - Ensure MySQL is installed and running.
   - Create a database named `securichat`:
     ```sql
     CREATE DATABASE securichat;
     ```
   - Create the necessary tables:
     ```sql
     USE securichat;

     CREATE TABLE user_status (
         username VARCHAR(50) PRIMARY KEY,
         last_seen DATETIME
     );

     CREATE TABLE messages (
         id INT AUTO_INCREMENT PRIMARY KEY,
         sender VARCHAR(50),
         receiver VARCHAR(50),
         content TEXT,
         message_type VARCHAR(20) DEFAULT 'text',
         file_path VARCHAR(255),
         file_size BIGINT,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
     );
     ```
   - Update the database credentials in `db.py` and `server.py` if needed (default user: `xatovate`, password: `123123`).

4. **Directory Setup**:
   - Ensure the `server_media` and `client_media` directories are writable for file storage.
   - Logs are automatically saved in the `logs` directory.

## Usage

1. **Start the Server**:
   Run the server script to start the chat server:
   ```bash
   python server.py
   ```
   The server listens on `127.0.0.1:12345` by default.

2. **Start the Client**:
   Run the client GUI to connect to the server:
   ```bash
   python SecuriChatGUI.py
   ```
   - Enter a username in the login screen.
   - Select a user from the list to start chatting.
   - Send text messages or attach files using the chat interface.

3. **Features in the GUI**:
   - **Login Screen**: Enter your username to connect to the server.
   - **User Selection**: View online/offline users and select a chat partner.
   - **Chat Screen**: Send/receive encrypted messages, attach files, and view chat history.
   - **File Transfer**: Use the 📎 button to send files (images, videos, audio, etc.).
   - **Download Files**: Click "Download" next to received file messages to retrieve files.

4. **Logs**:
   - Logs are saved in the `logs` directory with filenames like `chat_log_YYYYMMDD_HHMMSS.log`.
   - Logs include connection events, message exchanges, file transfers, encryption operations, and errors.

## Project Structure

- `SecuriChatGUI.py`: Client-side GUI and logic for connecting, chatting, and file transfers.
- `server.py`: Server-side logic for handling client connections, message routing, and file storage.
- `db.py`: Database operations for storing messages and file metadata.
- `logger.py`: Logging functionality for tracking all events.
- `crypto_utils.py`: Encryption (AES) and checksum (CRC32) utilities.

## Security

- **Encryption**: All messages and files are encrypted using Fernet (AES-based) with a derived key.
- **Error Detection**: CRC32 checksums ensure data integrity during transmission.
- **Database**: Messages are stored encrypted in the MySQL database.

## Notes

- The server must be running before clients can connect.
- Ensure the MySQL server is running and credentials are correct.
- File transfers are stored in `server_media` on the server and `client_media` on the client.
- The application uses a simple password-based key derivation for encryption. For production, consider using a more secure key management system.

## Troubleshooting

- **Connection Errors**: Verify the server is running and the host/port (`127.0.0.1:12345`) are correct.
- **Database Errors**: Check MySQL credentials and ensure the `securichat` database and tables are created.
- **File Transfer Issues**: Ensure write permissions for `server_media` and `client_media` directories.
- **Decryption Errors**: Verify the encryption key consistency across client and server.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for bugs, features, or improvements.

## Author

SecuriChat was created to provide a secure, user-friendly messaging platform with robust logging and encryption features.
by saleh mhosseini