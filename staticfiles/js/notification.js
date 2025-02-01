document.addEventListener('DOMContentLoaded', function () {
    const closeButtons = document.querySelectorAll('.notification__close');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.stopPropagation();

            let notification = button.closest('.notification');
            if (notification) {
                notification.style.display = 'none';
            }
        });
    });
});
