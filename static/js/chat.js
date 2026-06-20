const chatInput     = document.getElementById('chat-input');
const sendBtn       = document.getElementById('send-btn');
const messagesEl    = document.getElementById('messages');
const welcomeScreen = document.getElementById('welcome-screen');
const historyItems  = document.querySelectorAll('.history-item');
const newChatBtn    = document.getElementById('new-chat-btn');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar       = document.getElementById('sidebar');
const overlay       = document.getElementById('overlay');
const chips         = document.querySelectorAll('.chip');

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true });

// ── Sidebar (mobile) ─────────────────────────────────────
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
});
overlay.addEventListener('click', closeSidebar);

function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
}

// ── New consultation ─────────────────────────────────────
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

// ── Past consultations ────────────────────────────────────
historyItems.forEach(item => {
    item.addEventListener('click', () => {
        clearChat();
        welcomeScreen.style.display = 'none';
        appendUserMessage(item.dataset.question);
        appendAiReport(item.dataset.answer);
        closeSidebar();
    });
});

// ── Auto-resize textarea ─────────────────────────────────
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
    sendBtn.disabled = chatInput.value.trim() === '';
});

// ── Enter to send ────────────────────────────────────────
chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) sendMessage();
    }
});
sendBtn.addEventListener('click', sendMessage);

// ── Append user message ───────────────────────────────────
function appendUserMessage(text) {
    welcomeScreen.style.display = 'none';
    const row = document.createElement('div');
    row.className = 'message-row user';
    const bubble = document.createElement('div');
    bubble.className = 'bubble user-bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
}

// ── Append AI medical report (rendered markdown) ──────────
function appendAiReport(markdownText) {
    welcomeScreen.style.display = 'none';

    const row = document.createElement('div');
    row.className = 'message-row ai';

    const card = document.createElement('div');
    card.className = 'report-card';

    // Report header
    const header = document.createElement('div');
    header.className = 'report-header';
    header.innerHTML = `
        <div class="report-header-left">
            <div class="report-icon"><i class="fas fa-file-medical"></i></div>
            <div>
                <div class="report-title">AI Medical Report</div>
                <div class="report-sub">Tech.S MedAI · Powered by 5 AI Doctors</div>
            </div>
        </div>
        <div class="report-timestamp">${new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
    `;
    card.appendChild(header);

    // Report body — rendered markdown
    const body = document.createElement('div');
    body.className = 'report-body md-content';
    body.innerHTML = marked.parse(markdownText);
    card.appendChild(body);

    // Report footer
    const footer = document.createElement('div');
    footer.className = 'report-footer';
    footer.innerHTML = `<i class="fas fa-triangle-exclamation"></i> This is AI-generated guidance. Always consult a licensed physician for diagnosis and treatment.`;
    card.appendChild(footer);

    row.appendChild(card);
    messagesEl.appendChild(row);
    scrollToBottom();
}

// ── Typing indicator ─────────────────────────────────────
function showTyping() {
    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.id = 'typing-row';

    const card = document.createElement('div');
    card.className = 'report-card typing-card';
    card.innerHTML = `
        <div class="report-header">
            <div class="report-header-left">
                <div class="report-icon"><i class="fas fa-stethoscope fa-spin-pulse"></i></div>
                <div>
                    <div class="report-title">Consulting AI Doctors…</div>
                    <div class="report-sub">Gemini · Deepseek · Qwen · Sarvam · Meta AI</div>
                </div>
            </div>
        </div>
        <div class="typing-body">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <span class="typing-text">Analysing your symptoms across 5 models</span>
        </div>
    `;
    row.appendChild(card);
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
    if (!message) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;
    chatInput.disabled = true;

    appendUserMessage(message);
    showTyping();

    try {
        const res = await fetch('/chat/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat: message })
        });

        removeTyping();

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            appendAiReport('**Error:** ' + (err.error || 'Something went wrong. Please try again.'));
        } else {
            const data = await res.json();
            appendAiReport(data.ans || '_No response received._');
        }
    } catch (err) {
        removeTyping();
        appendAiReport('**Network error.** Please check your connection and try again.');
        console.error(err);
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = chatInput.value.trim() === '';
        chatInput.focus();
    }
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
