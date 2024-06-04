document.addEventListener('DOMContentLoaded', function () {
    const contactForm = document.getElementById('contact-form');
    const successMessage = document.getElementById('success-message');
    const url = contactForm.getAttribute('data-url');

    contactForm.addEventListener('submit', function (event) {

        event.preventDefault();

        const formData = new FormData(contactForm);

        fetch(url, {method: 'POST',body: formData})
        .then(response => {
            if (response.ok) {
                contactForm.reset();
                successMessage.style.display = 'block';

                setTimeout(function () {
                    successMessage.style.display = 'none';
                }, 5000);
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
