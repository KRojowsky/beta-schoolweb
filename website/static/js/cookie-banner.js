'use strict';

document.addEventListener('DOMContentLoaded', function() {
    if (!window.localStorage) {
        alert('Twoja przeglądarka nie obsługuje funkcji wymaganych do obsługi cookies.');
        return;
    }

    const cookieBanner = document.getElementById('cookie-consent-banner');
    const acceptButton = document.getElementById('accept-cookies');
    const rejectButton = document.getElementById('reject-cookies');

    if (!localStorage.getItem('cookiesAccepted')) {
        cookieBanner.style.display = 'block';
    }

    acceptButton.addEventListener('click', function() {
        localStorage.setItem('cookiesAccepted', 'true');
        cookieBanner.style.display = 'none';

        gtag('js', new Date());
        gtag('config', 'G-4H49J1BGY5', {
            'anonymize_ip': true
        });
        gtag('consent', 'update', {
            'analytics_storage': 'granted'
        });
    });

    rejectButton.addEventListener('click', function() {
        localStorage.setItem('cookiesAccepted', 'false');
        cookieBanner.style.display = 'none';

        gtag('consent', 'update', {
            'analytics_storage': 'denied'
        });
    });
});
