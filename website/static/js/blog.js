document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("theme-toggle-btn");
    const currentTheme = localStorage.getItem("theme") || "light";

    if (currentTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    if (toggleButton) {
        toggleButton.addEventListener("click", function () {
            document.body.classList.toggle("dark-mode");
            const theme = document.body.classList.contains("dark-mode") ? "dark" : "light";
            localStorage.setItem("theme", theme);
        });
    }

    const categoryMenuBtn = document.getElementById("category-menu-btn");
    const filterMenuBtn = document.getElementById("filter-menu-btn");
    const categoryMenu = document.getElementById("category-menu");
    const filterMenu = document.getElementById("filter-menu");

    function toggleMenu(menu) {
        if (menu) {
            menu.style.visibility = menu.style.visibility === "visible" ? "hidden" : "visible";
        }
    }

    function hideMenu(menu) {
        if (menu) {
            menu.style.visibility = "hidden";
        }
    }

    hideMenu(categoryMenu);
    hideMenu(filterMenu);

    if (categoryMenuBtn) {
        categoryMenuBtn.addEventListener("click", () => toggleMenu(categoryMenu));
    }

    if (filterMenuBtn) {
        filterMenuBtn.addEventListener("click", () => toggleMenu(filterMenu));
    }

    document.addEventListener("click", function (event) {
        if (
            categoryMenu && categoryMenuBtn &&
            !categoryMenu.contains(event.target) &&
            !categoryMenuBtn.contains(event.target)
        ) {
            hideMenu(categoryMenu);
        }

        if (
            filterMenu && filterMenuBtn &&
            !filterMenu.contains(event.target) &&
            !filterMenuBtn.contains(event.target)
        ) {
            hideMenu(filterMenu);
        }
    });

    const likeButton = document.getElementById("like-button");
    const likeCount = document.getElementById("like-count");

    if (likeButton && likeCount && typeof likePostUrl !== 'undefined' && typeof csrfToken !== 'undefined') {
        likeButton.addEventListener("click", function (event) {
            event.preventDefault();

            fetch(likePostUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json",
                },
                credentials: "same-origin",
            })
                .then((response) => response.json())
                .then((data) => {
                    likeCount.innerText = data.likes;
                    likeButton.classList.toggle("liked", data.liked);
                })
                .catch(() => {
                    alert("Błąd przy lajkowaniu posta.");
                });
        });
    }
});
