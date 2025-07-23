export let displayFrame;
export let videoFrames;
export let userIdInDisplayFrame = null;

export function setUserIdInDisplayFrame(id) {
    userIdInDisplayFrame = id;
}

export function initializeUI() {
    let messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    const memberContainer = document.getElementById('members__container');
    const memberButton = document.getElementById('members__button');

    const chatContainer = document.getElementById('messages__container');
    const chatButton = document.getElementById('chat__button');

    let activeMemberContainer = false;

    if (memberButton && memberContainer) {
        memberButton.addEventListener('click', () => {
            memberContainer.style.display = activeMemberContainer ? 'none' : 'block';
            activeMemberContainer = !activeMemberContainer;
        });
    }

    let activeChatContainer = false;

    if (chatButton && chatContainer) {
        chatButton.addEventListener('click', () => {
            chatContainer.style.display = activeChatContainer ? 'none' : 'block';
            activeChatContainer = !activeChatContainer;
        });
    }

    displayFrame = document.getElementById('stream__box');
    videoFrames = document.getElementsByClassName('video__container');

    initializeButtons();

    setupVideoFrames();
}

export function expandVideoFrame(e) {
    if (!displayFrame) return;

    let child = displayFrame.children[0];
    if (child) {
        document.getElementById('streams__container').appendChild(child);
    }

    displayFrame.style.display = 'block';
    displayFrame.appendChild(e.currentTarget);
    userIdInDisplayFrame = e.currentTarget.id;

    for (let i = 0; i < videoFrames.length; i++) {
        if (videoFrames[i].id !== userIdInDisplayFrame) {
            videoFrames[i].style.height = '100px';
            videoFrames[i].style.width = '100px';
        }
    }
}

function hideDisplayFrame() {
    if (!displayFrame) return;

    userIdInDisplayFrame = null;
    displayFrame.style.display = null;

    let child = displayFrame.children[0];
    if (child) {
        document.getElementById('streams__container').appendChild(child);
    }

    for (let i = 0; i < videoFrames.length; i++) {
        videoFrames[i].style.height = '300px';
        videoFrames[i].style.width = '300px';
    }
}

function setupVideoFrames() {
    if (!videoFrames || !displayFrame) return;

    for (let i = 0; i < videoFrames.length; i++) {
        videoFrames[i].addEventListener('click', expandVideoFrame);
    }

    displayFrame.addEventListener('click', hideDisplayFrame);
}

function initializeButtons() {
    const cameraBtn = document.getElementById("camera-btn");
    const micBtn = document.getElementById("mic-btn");
    const screenBtn = document.getElementById("screen-btn");

    const toggleButton = (button) => {
        if (button.id === "mic-btn") {
            if (button.classList.contains("active")) {
                // Mikrofon jest aktywny, przełącz na nieaktywny
                button.classList.remove("active");
                button.classList.add("disabled");
            } else {
                // Mikrofon jest nieaktywny, przełącz na aktywny
                button.classList.remove("disabled");
                button.classList.add("active");
            }
        } else {
            // Logika dla kamery i ekranu
            if (button.classList.contains("active")) {
                // Kamera/Ekran aktywne, przełącz na nieaktywne
                button.classList.remove("active");
                button.classList.add("disabled");
            } else {
                // Kamera/Ekran nieaktywne, przełącz na aktywne
                button.classList.remove("disabled");
                button.classList.add("active");
            }
        }
    };

    if (micBtn) micBtn.classList.add('active');  // Mikrofon domyślnie włączony
    if (cameraBtn) {
        cameraBtn.classList.remove('active');
        cameraBtn.classList.add('disabled'); // Kamera początkowo wyłączona
    }
    if (screenBtn) screenBtn.classList.add('disabled'); // Ekran początkowo wyłączony

    if (cameraBtn) {
        cameraBtn.addEventListener("click", function() {
            toggleButton(this); // Przełącz stan kamery
        });
    }

    if (micBtn) {
        micBtn.addEventListener("click", function() {
            toggleButton(this); // Przełącz stan mikrofonu
        });
    }

    if (screenBtn) {
        screenBtn.addEventListener("click", function() {
            toggleButton(this); // Przełącz stan ekranu
        });
    }
}
