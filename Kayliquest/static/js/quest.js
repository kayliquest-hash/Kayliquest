// =========================================
// KAYLI QUEST - QUÊTES
// =========================================

function claimQuest(questId, button) {

    button.disabled = true;
    button.textContent = "...";

    fetch("/quest/claim/" + questId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (!data.success) {
                button.disabled = false;
                button.textContent = "Réclamer";
                return;
            }

            const card = button.closest(".quest-card");
            card.classList.remove("ready");
            card.classList.add("claimed");

            button.className = "quest-btn done";
            button.textContent = "✓ Fait";

            showQuestToast(
                data.leveled_up
                    ? "Niveau supérieur ! Tu es maintenant niveau " + data.niveau
                    : "Quête accomplie ! +XP"
            );

            const xpFill = document.querySelector(".xp-fill");
            const xpLabel = document.querySelector(".xp-label");
            const levelBadge = document.querySelector(".level-badge");
            const questCount = document.querySelector(".quest-stat h2");

            if (xpFill) xpFill.style.width = data.xp + "%";
            if (xpLabel) xpLabel.textContent = data.xp + " / 100 XP";
            if (levelBadge) levelBadge.textContent = "Niv. " + data.niveau;
            if (questCount) questCount.textContent = data.quetes;

        })

        .catch(() => {
            button.disabled = false;
            button.textContent = "Réclamer";
        });

}

function showQuestToast(message) {

    const toast = document.createElement("div");
    toast.className = "quest-toast";
    toast.textContent = message;

    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add("show"));

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 2200);

}
