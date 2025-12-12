document.addEventListener('DOMContentLoaded', async () => {
    const statusEl = document.getElementById('status');
    const chatHistory = document.getElementById('chat-history');
    const inputEl = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');

    let currentVideoId = null;

    async function connectToCurrentTab() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (tab && tab.url && tab.url.includes('youtube.com/watch')) {
            const urlParams = new URLSearchParams(new URL(tab.url).search);
            const videoId = urlParams.get('v');

            if (videoId) {
                if (videoId !== currentVideoId) {
                    currentVideoId = videoId;
                    statusEl.textContent = 'Connected';
                    statusEl.className = 'status connected'; // Reset class
                    inputEl.disabled = false;
                    sendBtn.disabled = false;

                    // Clear history for new video
                    chatHistory.innerHTML = `
            <div class="message bot-message">
              Hello! I'm ready to answer questions about this video.
            </div>
          `;
                }
            } else {
                handleDisconnect('No Video ID');
            }
        } else {
            handleDisconnect('Not YouTube');
        }
    }

    function handleDisconnect(reason) {
        currentVideoId = null;
        statusEl.textContent = reason;
        statusEl.className = 'status error';
        inputEl.disabled = true;
        sendBtn.disabled = true;
    }

    // Initial connection
    connectToCurrentTab();

    // Listen for tab updates (navigation in same tab)
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
        if (changeInfo.status === 'complete' && tab.active) {
            connectToCurrentTab();
        }
    });

    // Listen for tab activation (switching tabs)
    chrome.tabs.onActivated.addListener(() => {
        connectToCurrentTab();
    });

    function appendMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message');
        msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        msgDiv.textContent = text;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function appendLoading() {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', 'bot-message');
        msgDiv.id = 'loading-msg';
        const span = document.createElement('span');
        span.classList.add('loading-dots');
        span.textContent = 'Thinking';
        msgDiv.appendChild(span);
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function removeLoading() {
        const loadingMsg = document.getElementById('loading-msg');
        if (loadingMsg) {
            loadingMsg.remove();
        }
    }

    async function handleSend() {
        const question = inputEl.value.trim();
        if (!question || !currentVideoId) return;

        appendMessage(question, 'user');
        inputEl.value = '';
        inputEl.disabled = true;
        sendBtn.disabled = true;

        appendLoading();

        try {
            const response = await fetch('http://localhost:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ video_id: currentVideoId, question: question })
            });

            const data = await response.json();
            removeLoading();

            if (response.ok) {
                appendMessage(data.answer, 'bot');
            } else {
                appendMessage('Error: ' + (data.error || 'Server error'), 'bot');
            }
        } catch (error) {
            removeLoading();
            appendMessage('Error: Could not connect to server. Make sure app.py is running.', 'bot');
        } finally {
            inputEl.disabled = false;
            sendBtn.disabled = false;
            inputEl.focus();
        }
    }

    sendBtn.addEventListener('click', handleSend);
    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
});
