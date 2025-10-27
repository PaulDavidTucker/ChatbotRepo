
(function() {
    // CSS Variables and Styling
    const customCSS = `
    :root {
        --primary-accent: #007bff;
        --secondary-accent: #0056b3;
        --background-light: rgba(255, 255, 255, 0.1);
        --text-primary: #ffffff;
        --text-secondary: #e0e0e0;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    /* Your custom styling */
    .chatbot-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .chatbot-widget {
        position: fixed;
        bottom: 25px;
        right: var(--position-right, 25px);
        left: var(--position-left, auto);
        background: linear-gradient(90deg, var(--primary-color, #007bff), var(--secondary-accent, #0056b3));
        color: white;
        width: 85px;
        height: 85px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 28px;
        box-shadow: 0 5px 20px rgba(0, 119, 255, 0.3);
        cursor: pointer;
        z-index: 1000;
        transition: transform 0.3s ease, bottom 0.3s ease, right 0.3s ease;
        border: none;
        outline: none;
    }

    .chatbot-widget:hover {
        transform: scale(1.1);
    }

    .chat-window {
        position: fixed;
        bottom: 100px;
        right: var(--position-right, 25px);
        left: var(--position-left, auto);
        width: 370px;
        max-width: calc(100% - 40px);
        height: 38em;
        max-height: calc(100% - 200px);
        background: linear-gradient(135deg, rgba(11, 11, 26, 0.6), rgba(11, 11, 26, 0.4));
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        z-index: 1001;
        transform: scale(0);
        transform-origin: bottom right;
        transition: transform 0.3s ease-in-out;
    }

    .chat-window.open {
        transform: scale(1);
    }

    .chat-header {
        background: var(--background-light);
        color: var(--text-primary);
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chat-header h3 {
        color: var(--text-primary);
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .close-chat-btn {
        background: none;
        border: none;
        color: var(--text-secondary);
        font-size: 1.8rem;
        cursor: pointer;
        transition: color 0.3s ease;
    }

    .close-chat-btn:hover {
        color: var(--text-primary);
    }

    .chat-body {
        flex-grow: 1;
        padding: 1rem 1.5rem;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }

    .chat-message {
        padding: 0.7rem 1.1rem;
        border-radius: 18px;
        max-width: 80%;
        line-height: 1.5;
        font-size: 0.95rem;
    }

    .chat-message.bot {
        background: var(--background-light);
        color: var(--text-secondary);
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        white-space: pre-line;
        word-wrap: break-word;
    }

    .chat-message.user {
        background: var(--primary-color, #007bff);
        color: #fff;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }

    .chat-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid var(--border-color);
    }

    .chat-footer form {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .chat-footer input {
        flex-grow: 1;
        background-color: rgba(0, 0, 0, 0.2);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        font-size: 1rem;
        font-family: inherit;
        transition: border-color 0.3s ease;
    }

    .chat-footer input:focus {
        outline: none;
        border-color: var(--primary-color, #007bff);
    }

    .chat-footer input::placeholder {
        color: var(--text-secondary);
        opacity: 0.7;
    }

    .chat-footer button {
        background: var(--primary-color, #007bff);
        color: #fff;
        border: none;
        border-radius: 8px;
        width: 60px;
        height: 60px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 1.2rem;
        cursor: pointer;
        transition: opacity 0.3s ease;
    }

    .chat-footer button:hover {
        opacity: 0.8;
    }

    .loading-dots {
        display: flex;
        gap: 4px;
        justify-content: center;
        align-items: center;
        padding: 0.5rem;
    }

    .loading-dots span {
        width: 6px;
        height: 6px;
        background-color: var(--text-secondary);
        border-radius: 50%;
        animation: loading-bounce 1.4s infinite ease-in-out both;
    }

    .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
    .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes loading-bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }

    @media (max-width: 768px) {
        .chatbot-widget {
            bottom: 15px;
            right: 15px;
            width: 55px;
            height: 55px;
            font-size: 26px;
        }

        .chat-window {
            width: auto;
            left: 15px;
            right: 15px;
            bottom: 85px;
            transform-origin: bottom center;
        }
    }
    `;

    // Inject CSS
    const style = document.createElement('style');
    style.textContent = customCSS;
    document.head.appendChild(style);

    // Widget initialization function
    window.initChatbot = function(config) {
        // Set CSS variables based on config
        document.documentElement.style.setProperty('--primary-color', config.primaryColor || '#007bff');
        document.documentElement.style.setProperty('--position-right', config.position?.includes('right') ? '25px' : 'auto');
        document.documentElement.style.setProperty('--position-left', config.position?.includes('left') ? '25px' : 'auto');

        // Create container
        const container = document.createElement('div');
        container.className = 'chatbot-container';
        container.style.cssText = `
            --primary-color: ${config.primaryColor || '#007bff'};
            --position-right: ${config.position?.includes('right') ? '25px' : 'auto'};
            --position-left: ${config.position?.includes('left') ? '25px' : 'auto'};
        `;
        document.body.appendChild(container);

        // Create widget button
        const button = document.createElement('button');
        button.className = 'chatbot-widget';
        button.innerHTML = '💬';
        button.onclick = toggleChat;
        button.setAttribute('aria-label', 'Open chat widget');
        container.appendChild(button);

        // Create chat window
        const chatWindow = document.createElement('div');
        chatWindow.className = 'chat-window';

        chatWindow.innerHTML = `
            <div class="chat-header">
                <h3>${config.title || 'AI Assistant'}</h3>
                <button class="close-chat-btn" aria-label="Close chat">&times;</button>
            </div>
            <div class="chat-body" id="chat-messages"></div>
            <div class="chat-footer">
                <form id="chat-form">
                    <input type="text" id="chat-input" placeholder="Type a message..." autocomplete="off">
                    <button type="submit" aria-label="Send message">→</button>
                </form>
            </div>
        `;

        container.appendChild(chatWindow);

        // Initialize chat functionality
        const messagesContainer = chatWindow.querySelector('#chat-messages');
        const input = chatWindow.querySelector('#chat-input');
        const form = chatWindow.querySelector('#chat-form');
        const closeBtn = chatWindow.querySelector('.close-chat-btn');

        let socket = null;
        let isConnected = false;
        let messageQueue = [];
        let currentBotMessage = null;

        function initializeWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = `${wsProtocol}${config.apiEndpoint}/ws/chat/${config.apiKey}/?domain=${encodeURIComponent(window.location.hostname)}`;

            socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log('Connected to chatbot service');
                isConnected = true;
                // Process any queued messages
                while (messageQueue.length > 0) {
                    socket.send(messageQueue.shift());
                }
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };

            socket.onclose = () => {
                console.log('Disconnected from chatbot service');
                isConnected = false;
                addMessage('Connection lost. Please refresh the page to reconnect.', 'bot');
            };

            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                addMessage('Connection error. Please try again.', 'bot');
            };
        }

        function handleMessage(data) {
            if (data.type === 'welcome') {
                addMessage(data.message, 'bot');
            } else if (data.type === 'start') {
                // Start of streaming response
                addLoadingMessage();
            } else if (data.type === 'chunk') {
                updateBotMessage(data.content);
            } else if (data.type === 'end') {
                // End of streaming response
                finalizeBotMessage();
            } else if (data.message) {
                addMessage(data.message, 'bot');
            }
        }

        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${sender}`;
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();

            if (sender === 'bot') {
                currentBotMessage = messageDiv;
            }
        }

        function addLoadingMessage() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-message bot';
            loadingDiv.innerHTML = `
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messagesContainer.appendChild(loadingDiv);
            currentBotMessage = loadingDiv;
            scrollToBottom();
        }

        function updateBotMessage(content) {
            if (currentBotMessage) {
                // If it's a loading message, replace with actual content
                if (currentBotMessage.querySelector('.loading-dots')) {
                    currentBotMessage.innerHTML = '';
                    currentBotMessage.textContent = content;
                } else {
                    // Append to existing content
                    currentBotMessage.textContent += content;
                }
                scrollToBottom();
            }
        }

        function finalizeBotMessage() {
            currentBotMessage = null;
        }

        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function sendMessage(message) {
            if (!message.trim()) return;

            addMessage(message, 'user');

            const messageData = JSON.stringify({
                message: message,
                metadata: {
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                }
            });

            if (isConnected && socket.readyState === WebSocket.OPEN) {
                socket.send(messageData);
            } else {
                messageQueue.push(messageData);
                if (!socket || socket.readyState === WebSocket.CLOSED) {
                    initializeWebSocket();
                }
            }
        }

        function toggleChat() {
            const isOpen = chatWindow.classList.contains('open');
            if (isOpen) {
                chatWindow.classList.remove('open');
            } else {
                chatWindow.classList.add('open');
                input.focus();

                // Initialize WebSocket connection when chat is first opened
                if (!socket) {
                    initializeWebSocket();
                }
            }
        }

        // Event listeners
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = input.value.trim();
            if (message) {
                sendMessage(message);
                input.value = '';
            }
        });

        closeBtn.addEventListener('click', toggleChat);

        // Add initial welcome message
        setTimeout(() => {
            if (messagesContainer.children.length === 0) {
                addMessage(config.welcomeMessage || 'Hello! How can I help you?', 'bot');
            }
        }, 100);
    };
})();
