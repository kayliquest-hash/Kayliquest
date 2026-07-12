// =========================================
// KAYLI QUEST - MESSAGERIE
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");

    if (!chatMessages) return;

    scrollToBottom();

    const conversationId = chatMessages.dataset.conversationId;

    // --- Envoi via AJAX (pas de rechargement de page) ---

    chatForm.addEventListener("submit", (e) => {

        e.preventDefault();

        const content = chatInput.value.trim();
        if (!content) return;

        chatInput.value = "";
        chatInput.disabled = true;

        fetch(window.location.pathname, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "content=" + encodeURIComponent(content)
        })
            .then(() => {
                chatInput.disabled = false;
                chatInput.focus();
                poll();
            })
            .catch(() => {
                chatInput.disabled = false;
            });

    });

    // --- Polling léger pour récupérer les nouveaux messages ---

    function getLastId() {

        const rows = chatMessages.querySelectorAll("[data-msg-id]");
        if (!rows.length) return 0;

        let max = 0;

        rows.forEach(r => {
            const id = parseInt(r.dataset.msgId, 10);
            if (!isNaN(id) && id > max) max = id;
        });

        return max;
    }

    function poll() {

        const since = getLastId();

        fetch("/api/messages/poll/" + conversationId + "?since=" + since)

            .then(r => r.json())

            .then(data => {

                if (!data.success) return;

                let hasNew = false;

                data.messages.forEach(m => {
                    appendMessage(m, m.mine);
                    hasNew = true;
                });

                if (hasNew) scrollToBottom();

            })

            .catch(() => {});

    }

    setInterval(poll, 3000);

    function appendMessage(m, mine) {

        const emptyState = chatMessages.querySelector(".chat-empty");
        if (emptyState) emptyState.remove();

        const row = document.createElement("div");
        row.className = "msg-row " + (mine ? "mine" : "theirs");
        row.dataset.msgId = m.id;

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = m.content;

        row.appendChild(bubble);
        chatMessages.appendChild(row);

    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

});
