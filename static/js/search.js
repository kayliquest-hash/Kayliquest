// =========================================
// KAYLI QUEST - RECHERCHE
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("search-input");
    const rows = document.querySelectorAll(".search-row");
    const empty = document.getElementById("search-empty");

    input.addEventListener("input", () => {

        const q = input.value.trim().toLowerCase();
        let visibleCount = 0;

        rows.forEach(row => {

            const match = row.dataset.pseudo.includes(q);
            row.style.display = match ? "flex" : "none";
            if (match) visibleCount++;

        });

        empty.style.display = visibleCount === 0 ? "block" : "none";

    });

});
