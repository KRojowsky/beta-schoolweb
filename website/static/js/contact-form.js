document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("contact-form");
    const successMessage = document.getElementById("success-message");
    const errorMessage = document.getElementById("error-message");

    function hideMessages() {
        setTimeout(() => {
            successMessage.style.display = "none";
            errorMessage.style.display = "none";
        }, 5000);
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(form);

        fetch(form.dataset.url, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                successMessage.style.display = "block";
                errorMessage.style.display = "none";
                form.reset();
                hideMessages();
            } else {
                successMessage.style.display = "none";
                errorMessage.style.display = "block";
                errorMessage.textContent = data.message || "Wystąpił nieoczekiwany błąd.";
                hideMessages();
            }
        })
        .catch(error => {
            successMessage.style.display = "none";
            errorMessage.style.display = "block";
            errorMessage.textContent = "Wystąpił problem z przesłaniem formularza. Spróbuj ponownie.";
            hideMessages();
        });
    });
});
