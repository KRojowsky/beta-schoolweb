const hamburgerMenu = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.mobile-menu');


hamburgerMenu.addEventListener('click', () => {
  navLinks.classList.toggle('show');
  hamburgerMenu.classList.toggle('active');
});
