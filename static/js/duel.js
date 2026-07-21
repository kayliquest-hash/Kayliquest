// =========================================
// KAYLI QUEST - DUELS
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    const timerEl = document.querySelector(".duel-timer");

    if (timerEl && timerEl.dataset.deadline) {

        updateTimer(timerEl);
        setInterval(() => updateTimer(timerEl), 1000);

    }

});

function updateTimer(el) {

    const deadline = new Date(el.dataset.deadline).getTime();
    const now = Date.now();
    const diff = deadline - now;

    if (diff <= 0) {
        el.textContent = "00:00:00";
        // le temps est écoulé : on recharge pour laisser le serveur
        // faire avancer le statut du duel
        setTimeout(() => window.location.reload(), 1500);
        return;
    }

    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    el.textContent =
        String(hours).padStart(2, "0") + ":" +
        String(minutes).padStart(2, "0") + ":" +
        String(seconds).padStart(2, "0");

}

function respondDuel(duelId, action) {

    fetch("/duel/" + action + "/" + duelId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (data.success) {
                window.location.reload();
            }

        });

}
