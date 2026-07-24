// =========================================
// KAYLI QUEST - ADMINISTRATION
// =========================================

function toggleBan(userId, button) {

    button.disabled = true;

    fetch("/admin/toggle_ban/" + userId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            button.disabled = false;

            if (!data.success) return;

            button.classList.toggle("active-red", data.banned);

            const row = document.querySelector(`[data-user-row="${userId}"]`);
            row.classList.toggle("is-banned", data.banned);

            let badge = row.querySelector(".banned-badge");

            if (data.banned && !badge) {
                badge = document.createElement("span");
                badge.className = "banned-badge";
                badge.textContent = "Banni";
                row.querySelector(".admin-info h3").appendChild(badge);
            } else if (!data.banned && badge) {
                badge.remove();
            }

        })

        .catch(() => { button.disabled = false; });

}

function toggleAdmin(userId, button) {

    button.disabled = true;

    fetch("/admin/toggle_admin/" + userId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            button.disabled = false;

            if (!data.success) return;

            button.classList.toggle("active-gold", data.admin);

        })

        .catch(() => { button.disabled = false; });

}

function assignRank(userId, select) {

    select.disabled = true;

    const rankId = select.value;

    fetch("/admin/assign_rank/" + userId, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "rank_id=" + rankId
    })

        .then(r => r.json())

        .then(data => {
            select.disabled = false;
        })

        .catch(() => { select.disabled = false; });

}

function deleteRank(rankId, button) {

    if (!confirm("Supprimer définitivement ce rang ?")) return;

    button.disabled = true;

    fetch("/admin/delete_rank/" + rankId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (!data.success) {
                button.disabled = false;
                return;
            }

            const row = document.querySelector(`[data-rank-row="${rankId}"]`);
            row.classList.add("removing");
            setTimeout(() => row.remove(), 300);

        })

        .catch(() => { button.disabled = false; });

}

function deletePost(postId, button) {

    if (!confirm("Supprimer définitivement cette publication ?")) return;

    button.disabled = true;

    fetch("/admin/delete_post/" + postId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (!data.success) {
                button.disabled = false;
                return;
            }

            const row = document.querySelector(`[data-post-row="${postId}"]`);
            row.classList.add("removing");
            setTimeout(() => row.remove(), 300);

        })

        .catch(() => { button.disabled = false; });

}
