'use strict';

document.addEventListener('DOMContentLoaded', function() {
    if (typeof gtag !== 'function') return;

    const GA_ID = 'G-4H49J1BGY5';
    const consent = localStorage.getItem('cookiesAccepted');

    if (consent === 'true') {
        gtag('js', new Date());
        gtag('consent', 'update', { 'analytics_storage': 'granted' });
        gtag('config', GA_ID, { 'anonymize_ip': true });
    } else {
        gtag('consent', 'default', { 'analytics_storage': 'denied' });
    }
});
