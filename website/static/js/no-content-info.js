function openModal() {
    document.getElementById('no-content-info-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('no-content-info-modal').style.display = 'none';
}

window.onclick = function(event) {
    let modal = document.getElementById('no-content-info-modal');
    if (event.target == modal) {
        closeModal();
    }
};

document.querySelector('.close').addEventListener('click', closeModal);
