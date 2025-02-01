function openModal() {
    document.getElementById('shop-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('shop-modal').style.display = 'none';
}

window.onclick = function(event) {
    let modal = document.getElementById('shop-modal');
    if (event.target == modal) {
        closeModal();
    }
};

document.querySelector('.close').addEventListener('click', closeModal);
