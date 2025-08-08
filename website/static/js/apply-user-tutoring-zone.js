function selectRole(role) {
  document.getElementById('role-input').value = role;
  document.getElementById('form-fields').classList.remove('hidden');
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('selected'));
  document.querySelector(`[data-role="${role}"]`).classList.add('selected');

  if (role === 'student') {
    document.getElementById('age-confirmation-text').innerText =
      "Potwierdzam ukończenie 18 lat lub zgoda na założenie konta jest wyrażona przez rodzica/opiekuna.";
    document.getElementById('notes-field').style.display = 'block';
  } else {
    document.getElementById('age-confirmation-text').innerText =
      "Potwierdzam ukończenie 18 lat.";
    document.getElementById('notes-field').style.display = 'none';
  }

  document.getElementById('form-fields').style.display = 'block';
}

document.addEventListener('DOMContentLoaded', function () {
  const roleInput = document.getElementById('role-input');
  const role = roleInput.value;

  if (role) {
    document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('selected'));
    const selectedBtn = document.querySelector(`[data-role="${role}"]`);
    if (selectedBtn) selectedBtn.classList.add('selected');

    if (role === 'student') {
      document.getElementById('age-confirmation-text').innerText =
        "Potwierdzam ukończenie 18 lat lub zgoda na założenie konta jest wyrażona przez rodzica/opiekuna.";
      document.getElementById('notes-field').style.display = 'block';
    } else {
      document.getElementById('age-confirmation-text').innerText =
        "Potwierdzam ukończenie 18 lat.";
      document.getElementById('notes-field').style.display = 'none';
    }

    document.getElementById('form-fields').style.display = 'block';
  }
});
