document.querySelector('.chat-icon').addEventListener('click', function() {
    document.getElementById('chatPopup').style.display = 'block';
    document.querySelector('#chatInput').focus();
});

function closeChatPopup() {
    const chatPopup = document.getElementById('chatPopup');
    chatPopup.style.display = 'none';
    document.querySelector('.chat-icon').focus();
}

function addUserMessage(messageText) {
    appendUserMessage(messageText);
    checkUserMessage(messageText);
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('chatForm');
    const input = document.querySelector('#chatInput');

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const messageText = input.value.trim();

        if (messageText !== '') {
            appendUserMessage(messageText);
            input.value = '';

            checkUserMessage(messageText);
        }
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeChatPopup();
        }
    });
});

let cachedResponses = null;

async function fetchResponses() {
    if (!cachedResponses) {
        const response = await fetch('/static/json/responses.json');
        if (!response.ok) throw new Error('Wystąpiły problemy z siecią...');
        cachedResponses = await response.json();
    }
    return cachedResponses;
}

async function checkUserMessage(messageText) {
    const normalizedMessage = normalizeText(messageText);

    try {
        const data = await fetchResponses();
        const normalizedQuestions = data.questions.map(item => ({
            ...item,
            question: item.question.map(normalizeText)
        }));

        const matchedQuestion = normalizedQuestions.find(item =>
            item.question.some(q => normalizedMessage.includes(q))
        );

        if (matchedQuestion) {
            const randomAnswer = matchedQuestion.answers[Math.floor(Math.random() * matchedQuestion.answers.length)];
            sendMessageFromBot(randomAnswer);
        } else {
            sendMessageFromBot("Niestety nie znam jeszcze odpowiedzi na to pytanie...&#x1F97A;");
        }
    } catch (error) {
        console.error('Błąd przetwarzania treści:', error);
        sendMessageFromBot("Wystąpił błąd podczas przetwarzania wiadomości.");
    }
}

function normalizeText(text) {
    return text.toLowerCase()
               .replace(/[.,\/#!$%\^&\*;:{}=\-_~()]/g, "")
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
            <img src="${staticImagePath}" alt="ikona chatbota" class="chatbot-img" loading="lazy">
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
