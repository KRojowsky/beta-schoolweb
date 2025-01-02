const hamburgerMenu = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.mobile-menu');
const menuItems = document.querySelectorAll('.mobile-menu a');

// Funkcja do otwierania/zamykania menu
const toggleMenu = () => {
  navLinks.classList.toggle('show');
  hamburgerMenu.classList.toggle('active');
};

// Funkcja do zamykania menu po kliknięciu w element
const closeMenu = () => {
  navLinks.classList.remove('show');
  hamburgerMenu.classList.remove('active');
};

// Dodanie eventu do kliknięcia hamburgera
hamburgerMenu.addEventListener('click', toggleMenu);

// Dodanie eventu do kliknięcia w linki menu
menuItems.forEach(item => {
  item.addEventListener('click', closeMenu);
});
