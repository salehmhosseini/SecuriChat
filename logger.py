import logging
import os
from datetime import datetime
import json

class ChatLogger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        self.setup_logger()

    def setup_logger(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"chat_log_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_connection(self, username, status, details=None):
        message = f"Connection - User: {username}, Status: {status}"
        if details:
            message += f", Details: {json.dumps(details)}"
        self.logger.info(message)

    def log_message(self, sender, receiver, content_type, content, encrypted=False):
        message = f"Message - Sender: {sender}, Receiver: {receiver}, Type: {content_type}, Encrypted: {encrypted}, Content: {content}"
        self.logger.info(message)

    def log_file_transfer(self, sender, receiver, file_name, file_size, file_type):
        message = f"File Transfer - Sender: {sender}, Receiver: {receiver}, File: {file_name}, Size: {file_size}, Type: {file_type}"
        self.logger.info(message)

    def log_error(self, error_type, error_message):
        message = f"Error - Type: {error_type}, Message: {error_message}"
        self.logger.error(message)

    def log_encryption(self, operation, details):
        message = f"Encryption - Operation: {operation}, Details: {details}"
        self.logger.info(message)

    def log_checksum(self, operation, data, checksum):
        message = f"Checksum - Operation: {operation}, Data: {data[:50]}..., Checksum: {checksum}"
        self.logger.info(message)