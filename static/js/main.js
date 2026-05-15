const toggleHistoryBtn = document.getElementById('toggle-history');
const historySection = document.getElementById('history-section');

if (toggleHistoryBtn && historySection) {
    toggleHistoryBtn.addEventListener('click', () => {
        historySection.classList.toggle('show');
        toggleHistoryBtn.textContent = historySection.classList.contains('show') ? 'Hide Chat History' : 'View Chat History';
    });
}
const hamburger = document.getElementById('hamburger');
const nav = document.querySelector('nav');

if (hamburger && nav) {
    hamburger.addEventListener('click', () => {
        nav.classList.toggle('nav-open');
    });

    // Close menu when a link is clicked
    const navLinks = nav.querySelectorAll('a');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            nav.classList.remove('nav-open');
        });
    });
}

// Password visibility toggle
const passwordToggle = document.getElementById('password-toggle');
if (passwordToggle) {
    const passwordInput = document.getElementById('password');
    const icon = passwordToggle.querySelector('i');

    passwordToggle.addEventListener('click', (e) => {
        e.preventDefault();
        const isPassword = passwordInput.type === 'password';
        
        if (isPassword) {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
            passwordToggle.title = 'Hide Password';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
            passwordToggle.title = 'Show Password';
        }
    });
}

const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
    const body = document.body;
    const themeIcon = themeToggle.querySelector('i');
    const currentTheme = localStorage.getItem('theme') || 'dark';

    if (currentTheme === 'light') {
        body.classList.add('light-mode');
        themeIcon.className = 'fas fa-sun';
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('light-mode');

        if (body.classList.contains('light-mode')) {
            themeIcon.className = 'fas fa-sun';
            localStorage.setItem('theme', 'light');
        } else {
            themeIcon.className = 'fas fa-moon';
            localStorage.setItem('theme', 'dark');
        }
    });
}

const modelCards = document.querySelectorAll('.model-card');
const selectedModelInput = document.getElementById('selected-model');
if (modelCards.length && selectedModelInput) {
    const defaultCard = document.querySelector('.model-card[data-model="Qwen"]');
    if (defaultCard) {
        defaultCard.classList.add('selected');
        selectedModelInput.value = 'Qwen';
    }

    modelCards.forEach(card => {
        card.addEventListener('click', () => {
            modelCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedModelInput.value = card.dataset.model;
        });
    });
}

const chatForm = document.getElementById('chat-form');
if (chatForm) {
    const responseBox = document.getElementById('response-box');
    const sendButton = document.getElementById('send-button');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!selectedModelInput.value) {
            alert('Please select an AI model before sending your message.');
            return;
        }

        const message = document.getElementById('ai_chat').value.trim();
        if (!message) {
            alert('Please enter a message before sending.');
            return;
        }

        if (responseBox) {
            responseBox.textContent = 'Thinking...';
        }
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.textContent = 'Thinking...';
        }

        try {
            const response = await fetch('/chat/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    aimodel: selectedModelInput.value,
                    chat: message
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            if (responseBox) {
                responseBox.textContent = result.ans || 'No response received.';
            }
        } catch (error) {
            if (responseBox) {
                responseBox.textContent = 'There was an error. Please try again.';
            }
            console.error(error);
        } finally {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = 'Send Message';
            }
        }
    });
}
