const hamburgerMenu = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.mobile-menu');
const menuItems = document.querySelectorAll('.mobile-menu a');

const toggleMenu = () => {
  navLinks.classList.toggle('show');
  hamburgerMenu.classList.toggle('active');
  document.body.classList.toggle('no-scroll');
};

const closeMenu = () => {
  navLinks.classList.remove('show');
  hamburgerMenu.classList.remove('active');
};

hamburgerMenu.addEventListener('click', toggleMenu);

menuItems.forEach(item => {
  item.addEventListener('click', closeMenu);
});
