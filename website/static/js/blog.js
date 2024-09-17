// Change theme (light/dark)
document.addEventListener("DOMContentLoaded", function() {
    const toggleButton = document.getElementById("theme-toggle-btn");
    const currentTheme = localStorage.getItem("theme") || "light";

    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    toggleButton.addEventListener("click", function() {
        document.body.classList.toggle("dark-mode");
        const theme = document.body.classList.contains("dark-mode") ? "dark" : "light";
        localStorage.setItem("theme", theme);
    });
});

// Categories and filters
document.addEventListener('DOMContentLoaded', function() {
    const categoryMenuBtn = document.getElementById('category-menu-btn');
    const filterMenuBtn = document.getElementById('filter-menu-btn');
    const categoryMenu = document.getElementById('category-menu');
    const filterMenu = document.getElementById('filter-menu');

    function toggleMenu(menu) {
        if (menu.style.visibility === 'visible') {
            menu.style.visibility = 'hidden';
        } else {
            menu.style.visibility = 'visible';
        }
    }

    function hideMenu(menu) {
        menu.style.visibility = 'hidden';
    }

    hideMenu(categoryMenu);
    hideMenu(filterMenu);

    categoryMenuBtn.addEventListener('click', function() {
        toggleMenu(categoryMenu);
    });

    filterMenuBtn.addEventListener('click', function() {
        toggleMenu(filterMenu);
    });

    document.addEventListener('click', function(event) {
        if (!categoryMenuBtn.contains(event.target) && !categoryMenu.contains(event.target)) {
            hideMenu(categoryMenu);
        }

        if (!filterMenuBtn.contains(event.target) && !filterMenu.contains(event.target)) {
            hideMenu(filterMenu);
        }
    });
});


// Likes
document.getElementById('like-button').addEventListener('click', function(event) {
    event.preventDefault();
    fetch(likePostUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('like-count').innerText = data.likes;
        const likeButton = document.getElementById('like-button');
        if (data.liked) {
            likeButton.classList.add('liked');
        } else {
            likeButton.classList.remove('liked');
        }
    });
});