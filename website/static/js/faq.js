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