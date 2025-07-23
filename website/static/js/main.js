import { initializeUI } from './room2.js';
import { joinRoomInit, initializeRTCEventListeners } from './room2_rtc.js';
import { setupRTM, getMembers } from './room2_rtm.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("Initializing application...");

    initializeUI();

    initializeRTCEventListeners();

    if (document.readyState === 'complete') {
        initializeRoom();
    } else {
        window.addEventListener('load', initializeRoom);
    }
});

async function initializeRoom() {
    try {
        await joinRoomInit();

        setupRTM();

        await getMembers();
    } catch (error) {
        console.error("Error initializing room:", error);
    }
}
