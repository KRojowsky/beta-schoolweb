'use strict';

document.addEventListener('DOMContentLoaded', function () {
    if (!window.localStorage) {
        alert('Twoja przeglądarka nie obsługuje funkcji wymaganych do obsługi cookies.');
        return;
    }

    const cookieBanner = document.getElementById('cookie-consent-banner');
    const acceptButton = document.getElementById('accept-cookies');
    const rejectButton = document.getElementById('reject-cookies');
    const GA_ID = 'G-4H49J1BGY5';

    const loadGtagScript = () => {
        if (document.getElementById('gtag-script')) return;

        const script = document.createElement('script');
        script.id = 'gtag-script';
        script.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
        script.async = true;
        document.head.appendChild(script);

        script.onload = () => {
            window.dataLayer = window.dataLayer || [];
            function gtag() { dataLayer.push(arguments); }
            window.gtag = gtag;
            gtag('js', new Date());
            gtag('consent', 'update', { 'analytics_storage': 'granted' });
            gtag('config', GA_ID, { anonymize_ip: true });
        };
    };

    const consent = localStorage.getItem('cookiesAccepted');

    if (consent === null) {
        cookieBanner.style.display = 'block';
    } else if (consent === 'true') {
        loadGtagScript();
    }

    acceptButton.addEventListener('click', function () {
        console.log('Użytkownik zaakceptował cookies');
        localStorage.setItem('cookiesAccepted', 'true');
        cookieBanner.style.display = 'none';
        loadGtagScript();
    });

    rejectButton.addEventListener('click', function () {
        console.log('Użytkownik odrzucił cookies');
        localStorage.setItem('cookiesAccepted', 'false');
        cookieBanner.style.display = 'none';

        if (typeof gtag === 'function') {
            gtag('consent', 'update', { 'analytics_storage': 'denied' });
        }
    });
});
