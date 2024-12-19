function togglePasswordVisibility(passwordFieldId, iconId, pathId) {
  const passwordInput = document.getElementById(passwordFieldId);
  const toggleIcon = document.getElementById(iconId);
  const iconPath = document.getElementById(pathId);

  if (passwordInput.type === 'password') {
    passwordInput.type = 'text'; // Pokazuje hasło
    toggleIcon.style.fill = '#32CD32'; // Zielony kolor ikony
    iconPath.setAttribute("d", "M12 5C7 5 3 9 3 12c0 3 4 7 9 7s9-4 9-7c0-3-4-7-9-7zm0 10c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"); // Zmieniamy kształt ikony na "widoczność"
  } else {
    passwordInput.type = 'password'; // Ukrywa hasło
    toggleIcon.style.fill = '#FF0000'; // Czerwony kolor ikony
    iconPath.setAttribute("d", "M12 5C7 5 3 9 3 12c0 3 4 7 9 7s9-4 9-7c0-3-4-7-9-7zm0 10c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"); // Zmieniamy kształt ikony na "brak widoczności"
  }
}
