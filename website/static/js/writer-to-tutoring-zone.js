document.addEventListener("DOMContentLoaded", function () {
    const teacherBtn = document.getElementById("teacher-btn");
    const studentBtn = document.getElementById("student-btn");
    const form = document.getElementById("user-form");

    const userTypeInput = document.createElement("input");
    userTypeInput.type = "hidden";
    userTypeInput.name = "user_type";
    form.appendChild(userTypeInput);

    const notesField = document.getElementById("notes-field");  // pole dodatkowych uwag
    const ageConfirmationText = document.getElementById("age-confirmation-text"); // tekst przy checkboxie

    const formErrors = document.querySelector(".form__error");
    if (formErrors) {
        form.style.display = "block";
    }

    function resetSelection() {
        teacherBtn.classList.remove("selected");
        studentBtn.classList.remove("selected");
    }

    function toggleNotesField(role) {
        if (role === "student") {
            notesField.style.display = "block";
        } else {
            notesField.style.display = "none";
        }
    }

    function updateAgeConfirmationText(role) {
        if (role === "student") {
            ageConfirmationText.textContent = 'Potwierdzam ukończenie 18 lat lub zgoda na założenie konta jest wyrażona przez rodzica/opiekuna.';
        } else {
            ageConfirmationText.textContent = 'Potwierdzam ukończenie 18 lat.';
        }
    }

    function showForm(roleBtn, role) {
        resetSelection();
        roleBtn.classList.add("selected");
        form.style.display = "block";
        userTypeInput.value = role;
        document.cookie = "user_role=" + role + "; path=/";

        toggleNotesField(role);
        updateAgeConfirmationText(role);
    }

    function getCookie(name) {
        let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        if (match) return match[2];
        return null;
    }

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
});
