function selectRole(role) {
  document.getElementById('role-input').value = role;
  document.getElementById('form-fields').classList.remove('hidden');
  document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('selected'));
  document.querySelector(`[data-role="${role}"]`).classList.add('selected');

  if (role === 'student') {
    document.getElementById('age-confirmation-text').innerText =
      "Potwierdzam ukończenie 18 lat lub zgoda na założenie konta jest wyrażona przez rodzica/opiekuna.";
  } else {
    document.getElementById('age-confirmation-text').innerText =
      "Potwierdzam ukończenie 18 lat.";
  }

  document.getElementById('form-fields').style.display = 'block';
}
