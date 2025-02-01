document.addEventListener("DOMContentLoaded", function() {
  const teacherBtn = document.getElementById('teacher-btn');
  const studentBtn = document.getElementById('student-btn');

  const form = document.querySelector('form');
  const userTypeField = document.createElement('input');
  userTypeField.type = 'hidden';
  userTypeField.name = 'user_type';
  form.appendChild(userTypeField);

  teacherBtn.addEventListener('click', function() {
    userTypeField.value = 'teacher';
    teacherBtn.classList.add('selected');
    studentBtn.classList.remove('selected');
  });

  studentBtn.addEventListener('click', function() {
    userTypeField.value = 'student';
    studentBtn.classList.add('selected');
    teacherBtn.classList.remove('selected');
  });
});
