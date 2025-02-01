function selectRole(button) {
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('selected'));
  button.classList.add('selected');
  document.getElementById('role-input').value = button.getAttribute('data-role');
  updateFormContent();
}

function updateFormContent() {
  var role = document.getElementById('role-input').value;
  var formTitle = document.getElementById('form-title');
  var formTagline = document.getElementById('form-tagline');
  var subjectLabel = document.querySelector("label[for='id_subject']");

  if (role === 'teacher') {
    formTitle.innerText = 'Rejestracja Korepetytora';
    formTagline.innerHTML = 'Utwórz konto korepetytora, aby móc w pełni korzystać ze <i>Strefy Korepetycji</i>';
    subjectLabel.innerHTML = 'Wybierz przedmiot, z którego chcesz udzielać korepetycji';
  } else {
    formTitle.innerText = 'Rejestracja Ucznia';
    formTagline.innerHTML = 'Utwórz konto ucznia, aby móc w pełni korzystać ze <i>Strefy Korepetycji</i>';
    subjectLabel.innerHTML = 'Wybierz przedmiot, z którego chcesz otrzymywać korepetycje';
  }
}

window.onload = updateFormContent;
