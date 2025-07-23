'use strict';

document.addEventListener('DOMContentLoaded', function () {
    let logoutTime = 60 * 60 * 1000;
    let logoutTimer;

    function resetTimer() {
        clearTimeout(logoutTimer);
        logoutTimer = setTimeout(logoutUser, logoutTime);
    }

    function logoutUser() {
        window.location.href = logoutUrl;
    }

    ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetTimer);
    });

    resetTimer();
});
