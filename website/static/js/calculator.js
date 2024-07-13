function calculateEarnings() {
    const lessonsPerWeekInput = document.getElementById('lessonsPerWeek');
    let lessonsPerWeek = parseInt(lessonsPerWeekInput.value);

    if (isNaN(lessonsPerWeek) || lessonsPerWeek <= 0 || !Number.isInteger(lessonsPerWeek)) {
        alert("Wprowadzona liczba zajęć musi być dodatnią liczbą całkowitą!");
        lessonsPerWeekInput.value = "";
        return;
    }

    const hourlyRate = 50;
    const monthlyEarnings = (lessonsPerWeek * hourlyRate * 4) + (lessonsPerWeek / 5) * hourlyRate * 3;
    const resultText = `Zarobisz miesięcznie około: ${monthlyEarnings} zł`;

    const resultElement = document.getElementById('monthlyEarnings');
    resultElement.innerText = resultText;
    resultElement.classList.add('fadeIn');
}

document.addEventListener("DOMContentLoaded", function () {
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`info-${i}`).style.display = "none";
    }
});
