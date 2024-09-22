const hamburgerMenu = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.mobile-menu');
const menuItems = document.querySelectorAll('.mobile-menu a');

hamburgerMenu.addEventListener('click', () => {
  navLinks.classList.toggle('show');
  hamburgerMenu.classList.toggle('active');
});

menuItems.forEach(item => {
  item.addEventListener('click', () => {
    navLinks.classList.remove('show');
    hamburgerMenu.classList.remove('active');
  });
});
