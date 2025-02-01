'use strict';

document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('cookiesAccepted') === 'true') {
        gtag('js', new Date());
        gtag('config', 'G-4H49J1BGY5', {
            'anonymize_ip': true
        });
        gtag('consent', 'update', {
            'analytics_storage': 'granted'
        });
    } else {
        gtag('consent', 'default', {
            'analytics_storage': 'denied'
        });
    }
});
