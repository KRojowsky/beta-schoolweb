document.querySelector('.chat-icon').addEventListener('click', function() {
    document.getElementById('chatPopup').style.display = 'block';
});

function closeChatPopup() {
    document.getElementById('chatPopup').style.display = 'none';
}

function addUserMessage(messageText) {
    appendUserMessage(messageText);
    checkUserMessage(messageText);
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const input = document.querySelector('#chatInput');
    const responseContainer = document.querySelector('#response');

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const messageText = input.value.trim();

        if (messageText !== '') {
            appendUserMessage(messageText);
            input.value = '';

            checkUserMessage(messageText)
        }
    });
});

async function checkUserMessage(messageText) {
    const normalizedMessage = normalizeText(messageText);
    try {
        const response = await fetch('{% static "json/responses.json" %}');
        if (!response.ok) throw new Error('Wystąpiły problemy z siecią...');

        const data = await response.json();
        const { questions } = data;
        let matchedQuestion = null;

        questions.forEach(item => {
            item.question.forEach(q => {
                const normalizedQuestion = normalizeText(q);
                if (normalizedMessage.includes(normalizedQuestion)) {
                    matchedQuestion = item;
                }
            });
        });

        if (matchedQuestion) {
            const { answers } = matchedQuestion;
            const randomAnswer = answers[Math.floor(Math.random() * answers.length)];
            sendMessageFromBot(randomAnswer);
        } else {
            sendMessageFromBot("W trakcie tworzenia...");
        }
    } catch (error) {
        console.error('Błąd przetwarzania treści:', error);
        sendMessageFromBot("W trakcie tworzenia...");
    }
}

function normalizeText(text) {
    return text.toLowerCase()
               .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "")
               .replace(/ą/g, 'a').replace(/ć/g, 'c').replace(/ę/g, 'e')
               .replace(/ł/g, 'l').replace(/ń/g, 'n').replace(/ó/g, 'o')
               .replace(/ś/g, 's').replace(/ż/g, 'z').replace(/ź/g, 'z')
               .trim();
}

function appendUserMessage(message) {
    let chatMessages = document.getElementById('chatMessages');
    let messageDiv = document.createElement('div');
    messageDiv.className = 'message-user';
    messageDiv.innerHTML = `
        <div class="message-text">
            <p>${message}</p>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessageFromBot(messageText) {
    let chatMessages = document.getElementById('chatMessages');
    let messageDiv = document.createElement('div');
    messageDiv.className = 'message-bot';
    messageDiv.innerHTML = `
        <div class="chatbot-img-container">
            <img src="${staticImagePath}" alt="ikona chatbota" class="chatbot-img">
        </div>
        <div class="message-text">
            <p>${messageText}</p>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    setTimeout(function() {
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 1000);
}

function getCurrentTime() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

let staticImagePath = document.getElementById('static-image-path').value;
