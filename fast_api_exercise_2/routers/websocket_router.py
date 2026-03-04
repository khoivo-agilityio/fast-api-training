"""WebSocket routes for real-time communication."""

import logging
from typing import Annotated

import jwt
from auth import ALGORITHM, SECRET_KEY
from database import get_session
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
from models import User
from sqlmodel import Session
from websocket_manager import manager

router = APIRouter(tags=["WebSocket"])

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_user_from_token(token: str, session: Session) -> User | None:
    """
    Validate JWT token and return user.

    Args:
        token: JWT token
        session: Database session

    Returns:
        User object if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None

        from auth import get_user_by_username

        user = get_user_by_username(session, username)
        return user
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================


@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    session: Annotated[Session, Depends(get_session)],
) -> None:
    """
    WebSocket endpoint for real-time communication.

    Usage:
        ws://localhost:8000/ws/{your_jwt_token}

    Message format:
        {
            "type": "message" | "ping",
            "content": "message text",
            "recipient_id": 123  // optional, for private messages
        }
    """
    # Validate token
    user = await get_user_from_token(token, session)
    if not user or user.disabled:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect user
    await manager.connect(websocket, user.id, user.username)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "welcome",
                "message": f"Welcome {user.username}!",
                "online_users": manager.get_online_users(),
            },
            user.id,
        )

        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type", "message")

            if message_type == "ping":
                # Respond to ping with pong
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    user.id,
                )

            elif message_type == "message":
                # Handle chat message
                content = data.get("content", "")
                recipient_id = data.get("recipient_id")

                message = {
                    "type": "message",
                    "sender_id": user.id,
                    "sender_username": user.username,
                    "content": content,
                    "timestamp": data.get("timestamp"),
                }

                if recipient_id:
                    # Private message
                    await manager.send_personal_message(message, recipient_id)
                    # Echo back to sender
                    message["recipient_id"] = recipient_id
                    await manager.send_personal_message(message, user.id)
                else:
                    # Broadcast to all
                    await manager.broadcast(message)

            elif message_type == "get_online_users":
                # Return list of online users
                await manager.send_personal_message(
                    {
                        "type": "online_users",
                        "users": manager.get_online_users(),
                    },
                    user.id,
                )

            else:
                # Unknown message type
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    },
                    user.id,
                )

    except WebSocketDisconnect:
        manager.disconnect(user.id)
        await manager.broadcast_system_message(f"{user.username} left the chat")

    except Exception as e:
        logger.error(f"WebSocket error for user {user.username}: {e}")
        manager.disconnect(user.id)


# ============================================================================
# TEST PAGE
# ============================================================================


@router.get("/ws-test")
async def get_websocket_test_page() -> HTMLResponse:
    """
    Simple HTML page to test WebSocket connection.

    Usage:
        1. Login to get a token: POST /token
        2. Open: http://localhost:8000/ws-test
        3. Enter your token and connect
    """
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>WebSocket Test</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                #messages { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
                .message { margin: 5px 0; padding: 5px; }
                .system { color: #666; font-style: italic; }
                .sent { background: #e3f2fd; text-align: right; }
                .received { background: #f5f5f5; }
                input, button { padding: 10px; margin: 5px; }
                #token { width: 400px; }
                #messageInput { width: 500px; }
                .online-users { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>🔌 WebSocket Test Client</h1>
            
            <div>
                <input type="text" id="token" placeholder="Enter your JWT token" />
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <span id="status">Disconnected</span>
            </div>
            
            <div class="online-users">
                <strong>Online Users:</strong>
                <div id="onlineUsers">-</div>
            </div>
            
            <div id="messages"></div>
            
            <div>
                <input type="text" id="messageInput" placeholder="Type a message..." onkeypress="handleKeyPress(event)" />
                <button onclick="sendMessage()">Send</button>
                <button onclick="getOnlineUsers()">Refresh Users</button>
            </div>
            
            <script>
                let ws = null;
                const messagesDiv = document.getElementById('messages');
                const statusSpan = document.getElementById('status');
                const tokenInput = document.getElementById('token');
                const messageInput = document.getElementById('messageInput');
                const onlineUsersDiv = document.getElementById('onlineUsers');
                
                function connect() {
                    const token = tokenInput.value.trim();
                    if (!token) {
                        alert('Please enter a token');
                        return;
                    }
                    
                    ws = new WebSocket(`ws://localhost:8000/ws/${token}`);
                    
                    ws.onopen = function(event) {
                        statusSpan.textContent = '✅ Connected';
                        statusSpan.style.color = 'green';
                        addMessage('system', 'Connected to WebSocket');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        console.log('Received:', data);
                        
                        if (data.type === 'welcome') {
                            addMessage('system', data.message);
                            updateOnlineUsers(data.online_users);
                        } else if (data.type === 'message') {
                            const sender = data.sender_username || 'Unknown';
                            addMessage('received', `${sender}: ${data.content}`);
                        } else if (data.type === 'system') {
                            addMessage('system', data.text);
                        } else if (data.type === 'online_users') {
                            updateOnlineUsers(data.users);
                        } else if (data.type === 'item_created') {
                            addMessage('system', `📦 New item: "${data.item_title}" by ${data.owner_username}`);
                        } else if (data.type === 'item_updated') {
                            addMessage('system', `✏️ Item updated: "${data.item_title}" by ${data.owner_username}`);
                        } else if (data.type === 'pong') {
                            addMessage('system', 'Pong received');
                        }
                    };
                    
                    ws.onclose = function(event) {
                        statusSpan.textContent = '❌ Disconnected';
                        statusSpan.style.color = 'red';
                        addMessage('system', 'Disconnected from WebSocket');
                    };
                    
                    ws.onerror = function(error) {
                        addMessage('system', 'Error: ' + error.message);
                    };
                }
                
                function disconnect() {
                    if (ws) {
                        ws.close();
                        ws = null;
                    }
                }
                
                function sendMessage() {
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        alert('Not connected');
                        return;
                    }
                    
                    const message = messageInput.value.trim();
                    if (!message) return;
                    
                    const data = {
                        type: 'message',
                        content: message,
                        timestamp: new Date().toISOString()
                    };
                    
                    ws.send(JSON.stringify(data));
                    addMessage('sent', `You: ${message}`);
                    messageInput.value = '';
                }
                
                function getOnlineUsers() {
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        alert('Not connected');
                        return;
                    }
                    
                    ws.send(JSON.stringify({ type: 'get_online_users' }));
                }
                
                function addMessage(type, text) {
                    const div = document.createElement('div');
                    div.className = `message ${type}`;
                    div.textContent = text;
                    messagesDiv.appendChild(div);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }
                
                function updateOnlineUsers(users) {
                    if (users.length === 0) {
                        onlineUsersDiv.textContent = 'No users online';
                    } else {
                        onlineUsersDiv.innerHTML = users.map(u => 
                            `${u.username} (ID: ${u.user_id})`
                        ).join(', ');
                    }
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
                
                // Ping every 30 seconds to keep connection alive
                setInterval(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ 
                            type: 'ping',
                            timestamp: new Date().toISOString()
                        }));
                    }
                }, 30000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
