document.addEventListener('DOMContentLoaded', function () {
    const contactForm = document.getElementById('contact-form');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const url = contactForm.getAttribute('data-url');

    contactForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(contactForm);
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                successMessage.style.display = 'block';
                setTimeout(() => successMessage.style.display = 'none', 5000);
                errorMessage.style.display = 'none';
            } else {
                errorMessage.style.display = 'block';
                errorMessage.textContent = data.message;
                setTimeout(() => errorMessage.style.display = 'none', 5000);
            }
        })
        .catch(error => {
            errorMessage.style.display = 'block';
            errorMessage.textContent = 'Wystąpił błąd, spróbuj ponownie.';
            setTimeout(() => errorMessage.style.display = 'none', 5000);
        });
    });
});
