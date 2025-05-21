document.addEventListener('DOMContentLoaded', function() {
    // Connect to Socket.IO server
    const socket = io();
    const username = document.body.dataset.username;
    const partner = document.body.dataset.partner;
    
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const usersList = document.getElementById('users-list');
    
    // Scroll chat to bottom initially
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Handle sending messages
    if (sendButton && messageInput) {
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && partner) {
            // Emit the message to the server
            socket.emit('send_message', {
                receiver: partner,
                message: message
            });
            
            // Add the message to the UI immediately
            addMessage(username, message, new Date().toLocaleTimeString(), true);
            messageInput.value = '';
        }
    }

    // Handle received messages
    socket.on('receive_message', function(data) {
        // Only display if the message is from our current chat partner
        if (data.sender === partner || data.sender === username) {
            const isSent = data.sender === username;
            addMessage(data.sender, data.message, data.timestamp, isSent);
        }
    });

    // Handle user status changes
    socket.on('user_status_change', function(data) {
        // Update the user list if it exists
        if (usersList) {
            const rows = usersList.querySelectorAll('tr');
            rows.forEach(row => {
                if (row.cells[0].textContent === data.username) {
                    // Update status badge
                    const badge = row.cells[1].querySelector('.badge');
                    badge.className = `badge bg-${data.status === 'online' ? 'success' : 'secondary'}`;
                    badge.textContent = data.status;
                    
                    // Update last seen
                    if (data.status === 'offline' && data.last_seen) {
                        row.cells[2].textContent = data.last_seen;
                    } else if (data.status === 'online') {
                        row.cells[2].textContent = 'Now';
                    }
                }
            });
        }
        
        // Update the partner status in chat view if needed
        if (data.username === partner) {
            const statusBadge = document.getElementById('partner-status');
            if (statusBadge) {
                statusBadge.className = `badge bg-${data.status === 'online' ? 'success' : 'secondary'}`;
                statusBadge.textContent = data.status === 'online' ? 'Online' : 'Offline';
                
                // Show notification if partner comes online
                if (data.status === 'online') {
                    showNotification(`${partner} is now online`);
                }
            }
        }
    });

    // Helper function to add messages to the chat
    function addMessage(sender, message, timestamp, isSent) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${sender}</strong>
                <small class="text-muted">${timestamp}</small>
            </div>
            <div class="message-body">${message}</div>
        `;
        
        if (chatMessages) {
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Helper function to show notifications
    function showNotification(message) {
        if (!("Notification" in window)) {
            return;
        }
        
        if (Notification.permission === "granted") {
            new Notification(message);
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification(message);
                }
            });
        }
    }

    // Request notification permission on page load
    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
    }
});