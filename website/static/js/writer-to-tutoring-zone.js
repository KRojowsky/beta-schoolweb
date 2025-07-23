document.addEventListener("DOMContentLoaded", function () {
    const teacherBtn = document.getElementById("teacher-btn");
    const studentBtn = document.getElementById("student-btn");
    const form = document.getElementById("user-form");

    // Tworzymy ukryte pole dla user_type
    const userTypeInput = document.createElement("input");
    userTypeInput.type = "hidden";
    userTypeInput.name = "user_type";
    form.appendChild(userTypeInput);

    // Sprawdzenie, czy formularz zawiera błędy (czy Django wyrenderowało błędy)
    const formErrors = document.querySelector(".form__error");
    if (formErrors) {
        form.style.display = "block"; // Jeśli są błędy, formularz ma być widoczny
    }

    function resetSelection() {
        teacherBtn.classList.remove("selected");
        studentBtn.classList.remove("selected");
    }

    function showForm(roleBtn, role) {
        resetSelection();
        roleBtn.classList.add("selected");
        form.style.display = "block";
        userTypeInput.value = role; // Ustawienie wartości pola user_type

        // Zapisz rolę w cookies
        document.cookie = "user_role=" + role + "; path=/";
    }

    // Funkcja do odczytywania cookies
    function getCookie(name) {
        let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        if (match) return match[2];
        return null;
    }

    // Funkcja do usuwania cookies
    function deleteCookie(name) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
    }

    // Sprawdź, czy w cookies jest zapisana rola
    const selectedRole = getCookie('user_role');

    if (selectedRole === "teacher") {
        showForm(teacherBtn, "teacher");
    } else if (selectedRole === "student") {
        showForm(studentBtn, "student");
    }

    teacherBtn.addEventListener("click", function () {
        showForm(this, "teacher");
    });

    studentBtn.addEventListener("click", function () {
        showForm(this, "student");
    });

    // Usuwanie cookies po zakończeniu procesu
    // Możesz wywołać tę funkcję po przekierowaniu użytkownika do kolejnej strony
    // np. po zapisaniu danych do bazy lub po zakończeniu procesu rejestracji

    // Przykład: Po zakończeniu rejestracji, usuwamy cookie:
    // deleteCookie('user_role');
});
