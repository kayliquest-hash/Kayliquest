// =========================================
// KAYLI QUEST - PROFIL (bascule d'onglets)
// =========================================

// =========================================
// KAYLI QUEST - PROFIL (bascule d'onglets)
// =========================================

function toggleFollow(button) {

    const userId = button.dataset.userId;

    button.disabled = true;

    fetch("/api/follow/" + userId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            button.disabled = false;

            if (!data.success) return;

            button.dataset.following = data.following ? "1" : "0";
            button.classList.toggle("following", data.following);

        })

        .catch(() => {
            button.disabled = false;
        });

}

document.addEventListener("DOMContentLoaded", () => {

    const tabBtns = document.querySelectorAll("[data-tab-btn]");
    const panels = document.querySelectorAll("[data-tab-panel]");

    tabBtns.forEach(btn => {

        btn.addEventListener("click", () => {

            const target = btn.dataset.tabBtn;

            tabBtns.forEach(b => b.classList.toggle("active", b === btn));

            panels.forEach(p => {
                p.hidden = p.dataset.tabPanel !== target;
            });

        });

    });

});
