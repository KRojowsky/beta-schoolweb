function togglePasswordVisibility() {
  const passwordInput = document.getElementById("password");
  const togglePasswordBtn = document.querySelector(".toggle-password");

  if (passwordInput.type === "password") {
    passwordInput.type = "text";
    togglePasswordBtn.classList.add("visible");
  } else {
    passwordInput.type = "password";
    togglePasswordBtn.classList.remove("visible");
  }
}