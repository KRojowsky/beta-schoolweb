function togglePasswordVisibility(passwordFieldId, iconId, pathId) {
    const passwordInput = document.getElementById(passwordFieldId);
    const toggleIcon = document.getElementById(iconId);
    const iconPath = document.getElementById(pathId);

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.style.fill = '#32CD32';
    } else {
        passwordInput.type = 'password';
        toggleIcon.style.fill = '#FF0000';
    }
}
