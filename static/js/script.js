document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".card");
    
    cards.forEach(card => {
        card.addEventListener("click", function () {
            alert(`You clicked on ${card.dataset.role} dashboard!`);
        });
    });
});
