const faqs = document.querySelectorAll(".faq")

faqs.forEach((faq) => {
    faq.addEventListener("click", () => {
    faq.classList.toggle("active");
    })
})

const hamburgerMenu = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.nav-links');
const navOptions = navLinks.querySelectorAll('.nav-option');

hamburgerMenu.addEventListener('click', () => {
  navLinks.classList.toggle('show');
});

navOptions.forEach(option => {
  option.addEventListener('click', () => {
    navLinks.classList.remove('show');
  });
});


function calculateEarnings() {
    const lessonsPerWeek = document.getElementById('lessonsPerWeek').value;
    const hourlyRate = 40;
    const monthlyEarnings = (lessonsPerWeek * hourlyRate * 4) + (lessonsPerWeek/5)*hourlyRate*3
    const resultText = `Zarobisz miesięcznie około: ${monthlyEarnings} zł`;

    const resultElement = document.getElementById('monthlyEarnings');
    resultElement.innerText = resultText;
    resultElement.classList.add('fadeIn');
}

document.addEventListener("DOMContentLoaded", function () {
    for (let i = 1; i <= 5; i++) {
      document.getElementById(`info-${i}`).style.display = "none";
    }
});


function toggleInfo(id) {
    var info = document.getElementById(`info-${id}`);
    var icon = document.getElementById(`toggle-icon-${id}`);
    if (info.style.display === "none" || info.style.display === "") {
      info.style.display = "block";
      icon.innerHTML = "&#9650;";
    } else {
      info.style.display = "none";
      icon.innerHTML = "&#9660;";
    }
}