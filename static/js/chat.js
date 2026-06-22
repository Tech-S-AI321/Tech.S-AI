const selectedModelInput = document.getElementById('selected-model');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const messagesEl = document.getElementById('messages');
const welcomeScreen = document.getElementById('welcome-screen');
const topbarModelImg = document.getElementById('topbar-model-img');
const topbarModelName = document.getElementById('topbar-model-name');
const modelItems = document.querySelectorAll('.model-item');
const historyItems = document.querySelectorAll('.history-item');
const newChatBtn = document.getElementById('new-chat-btn');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const chips = document.querySelectorAll('.chip');

const modelImages = {
    'Gemini':    '/static/gemini.png',
    'ChatGPT':   '/static/chatgpt.png',
    'Deepseek':  '/static/deepseek.png',
    'Qwen':      '/static/qwen.png',
    'Meta Ai':   '/static/metaai.png',
    'Sarvam':    '/static/sarvam.png',
};

function getModelImg(model) {
    return modelImages[model] || '/static/logo.jpeg';
}

// ── Model selection ──────────────────────────────────────
modelItems.forEach(item => {
    item.addEventListener('click', () => {
        modelItems.forEach(m => m.classList.remove('active'));
        item.classList.add('active');
        const model = item.dataset.model;
        selectedModelInput.value = model;
        topbarModelName.textContent = model;
        topbarModelImg.src = getModelImg(model);
        closeSidebar();
    });
});

// ── Sidebar toggle (mobile) ──────────────────────────────
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
});

overlay.addEventListener('click', closeSidebar);

function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
}

// ── New chat ─────────────────────────────────────────────
newChatBtn.addEventListener('click', () => {
    clearChat();
    closeSidebar();
    chatInput.focus();
});

function clearChat() {
    messagesEl.innerHTML = '';
    messagesEl.appendChild(welcomeScreen);
    welcomeScreen.style.display = 'flex';
}

// ── Suggestion chips ─────────────────────────────────────
chips.forEach(chip => {
    chip.addEventListener('click', () => {
        chatInput.value = chip.dataset.text;
        chatInput.dispatchEvent(new Event('input'));
        chatInput.focus();
    });
});

// ── History items ─────────────────────────────────────────
historyItems.forEach(item => {
    item.addEventListener('click', () => {
        const question = item.dataset.question;
        const answer = item.dataset.answer;
        const model = item.dataset.model;

        clearChat();
        welcomeScreen.style.display = 'none';

        appendMessage('user', question, model);
        appendMessage('ai', answer, model);
        closeSidebar();

        if (model) {
            selectedModelInput.value = model;
            topbarModelName.textContent = model;
            topbarModelImg.src = getModelImg(model);
            modelItems.forEach(m => {
                m.classList.toggle('active', m.dataset.model === model);
            });
        }
    });
});

// ── Auto-resize textarea ─────────────────────────────────
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
    sendBtn.disabled = chatInput.value.trim() === '';
});

// ── Send on Enter (Shift+Enter = newline) ────────────────
chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

// ── Append message ───────────────────────────────────────
function appendMessage(role, text, model) {
    welcomeScreen.style.display = 'none';

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    if (role === 'ai') {
        const avatar = document.createElement('img');
        avatar.className = 'ai-avatar';
        avatar.src = getModelImg(model || selectedModelInput.value);
        avatar.alt = 'AI';
        row.appendChild(avatar);
    }

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (role === 'ai') {
        bubble.classList.add('markdown');
        bubble.innerHTML = marked.parse(text);
    } else {
        bubble.textContent = text;
    }
    row.appendChild(bubble);

    messagesEl.appendChild(row);
    scrollToBottom();
}

// ── Typing indicator ─────────────────────────────────────
function showTyping(model) {
    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.id = 'typing-row';

    const avatar = document.createElement('img');
    avatar.className = 'ai-avatar';
    avatar.src = getModelImg(model || selectedModelInput.value);
    avatar.alt = 'AI';
    row.appendChild(avatar);

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    row.appendChild(bubble);

    messagesEl.appendChild(row);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById('typing-row');
    if (el) el.remove();
}

// ── Send message ─────────────────────────────────────────
async function sendMessage() {
    const message = chatInput.value.trim();
    const model = selectedModelInput.value;
    if (!message) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;
    chatInput.disabled = true;

    appendMessage('user', message, model);
    showTyping(model);

    try {
        const res = await fetch('/chat/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ aimodel: model, chat: message })
        });

        removeTyping();

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            appendMessage('ai', 'Error: ' + (err.error || 'Something went wrong. Please try again.'), model);
        } else {
            const data = await res.json();
            appendMessage('ai', data.ans || 'No response received.', model);
        }
    } catch (err) {
        removeTyping();
        appendMessage('ai', 'Network error. Please check your connection and try again.', model);
        console.error(err);
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = chatInput.value.trim() === '';
        chatInput.focus();
    }
}

// ── Scroll helpers ───────────────────────────────────────
function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
