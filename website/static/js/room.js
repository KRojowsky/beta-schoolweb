function displaySelectedFileName() {
    const imageInput = document.getElementById('image');
    const fileInput = document.getElementById('file');
    const selectedFileName = document.getElementById('selected-file-name');
    let fileName = '';

    if (imageInput.files.length > 0) {
        fileName = imageInput.files[0].name;
    } else if (fileInput.files.length > 0) {
        fileName = fileInput.files[0].name;
    }

    if (fileName) {
        const maxLength = 20;
        const truncatedFileName = fileName.length > maxLength ? fileName.slice(0, maxLength) + '...' : fileName;
        selectedFileName.textContent = truncatedFileName;
    } else {
        selectedFileName.textContent = '';
    }
}
