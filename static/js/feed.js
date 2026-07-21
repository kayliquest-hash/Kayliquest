// =========================================
// KAYLI QUEST - FEED
// =========================================

document.addEventListener("DOMContentLoaded", () => {
    setupFeedTabs();
    setupViewTracking();
    setupDoubleTapLike();
    setupShare();
    setupCaptionToggle();
    setupKayliVideos();
});

// --- Bascule Posts / Kayli ---

function setupFeedTabs() {

    const tabs = document.querySelectorAll("[data-feed-tab]");
    const panels = document.querySelectorAll("[data-feed-panel]");

    if (!tabs.length) return;

    tabs.forEach(tab => {

        tab.addEventListener("click", () => {

            const target = tab.dataset.feedTab;

            tabs.forEach(t => t.classList.toggle("active", t === tab));

            panels.forEach(p => {
                p.hidden = p.dataset.feedPanel !== target;
            });

            if (target === "kayli") {
                // reprend la lecture de la vidéo actuellement visible
                requestAnimationFrame(playVisibleKayliVideo);
            } else {
                // quitte l'onglet Kayli : coupe toutes les vidéos
                document.querySelectorAll("video[data-kayli-video]").forEach(v => v.pause());
            }

        });

    });

}

// --- Vue comptabilisée dès qu'une carte/post est bien visible ---

function setupViewTracking() {

    const cards = document.querySelectorAll(".post-card, .kayli-post");
    if (!cards.length) return;

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
                markViewed(entry.target.dataset.postId);
            }

        });

    }, { threshold: [0, 0.5] });

    cards.forEach(c => observer.observe(c));

}

// --- Onglet Kayli : lecture vidéo isolée dans son propre conteneur ---

let kayliMuted = true;

function setupKayliVideos() {

    const scrollBox = document.getElementById("kayli-scroll");
    const videos = document.querySelectorAll("video[data-kayli-video]");

    if (!scrollBox || !videos.length) return;

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            const video = entry.target;
            const post = video.closest(".kayli-post");

            if (entry.isIntersecting && entry.intersectionRatio >= 0.7) {
                video.muted = kayliMuted;
                video.play().catch(() => {
                    // lecture non-coupée refusée par le navigateur : on retente en muet
                    video.muted = true;
                    video.play().catch(() => {});
                });
                markViewed(post.dataset.postId);
            } else {
                video.pause();
            }

        });

    }, { root: scrollBox, threshold: [0, 0.7, 1] });

    videos.forEach(v => observer.observe(v));

    // Tap simple = pause / lecture
    document.querySelectorAll(".kayli-media-wrapper").forEach(wrapper => {

        const video = wrapper.querySelector("video[data-kayli-video]");
        const indicator = wrapper.querySelector(".kayli-play-indicator");
        if (!video) return;

        wrapper.addEventListener("click", (e) => {

            if (e.detail === 2) return; // laisse le double-tap gérer le like

            if (video.paused) {
                video.play().catch(() => {});
                indicator.classList.remove("show");
            } else {
                video.pause();
                indicator.classList.add("show");
            }

        });

    });

}

function toggleKayliMute(event, button) {

    event.stopPropagation();

    kayliMuted = !kayliMuted;

    // s'applique à la vidéo actuelle ET à toutes les suivantes
    document.querySelectorAll("video[data-kayli-video]").forEach(v => {
        v.muted = kayliMuted;
    });

    document.querySelectorAll("[data-mute-btn]").forEach(btn => {
        btn.classList.toggle("is-muted", kayliMuted);
    });

}

function playVisibleKayliVideo() {

    const scrollBox = document.getElementById("kayli-scroll");
    if (!scrollBox) return;

    const posts = scrollBox.querySelectorAll(".kayli-post");

    for (const post of posts) {

        const rect = post.getBoundingClientRect();
        const boxRect = scrollBox.getBoundingClientRect();

        if (rect.top >= boxRect.top - 5 && rect.top <= boxRect.top + 5) {
            const video = post.querySelector("video[data-kayli-video]");
            if (video) video.play().catch(() => {});
            break;
        }

    }

}

// --- Double-tap sur le média (post ou vidéo Kayli) = like ---

function setupDoubleTapLike() {

    document.querySelectorAll(".post-card, .kayli-post").forEach(card => {

        const media = card.querySelector(".card-media, .kayli-media-wrapper");
        if (!media) return;

        const burst = card.querySelector(".heart-burst");
        const postId = card.dataset.postId;

        let lastTap = 0;

        media.addEventListener("click", () => {

            const now = Date.now();

            if (now - lastTap < 300) {

                triggerHeartBurst(burst);

                const likeBtn = card.querySelector("[data-like-btn]");
                if (likeBtn.dataset.liked !== "1") {
                    likePost(postId, likeBtn);
                }

            }

            lastTap = now;

        });

    });

}

function triggerHeartBurst(burst) {
    if (!burst) return;
    burst.classList.remove("burst");
    void burst.offsetWidth;
    burst.classList.add("burst");
    setTimeout(() => burst.classList.remove("burst"), 700);
}

// --- Like ---

function likePost(postId, button) {

    button.classList.add("like-animation");
    setTimeout(() => button.classList.remove("like-animation"), 400);

    fetch("/api/like/" + postId)

        .then(r => r.json())

        .then(data => {

            if (!data.success) return;

            document.querySelectorAll(`[data-like-btn][onclick*="likePost(${postId},"]`).forEach(btn => {
                btn.dataset.liked = data.liked ? "1" : "0";
                btn.classList.toggle("liked", data.liked);
            });

            document.querySelectorAll("#likes-" + postId).forEach(span => {
                span.textContent = formatCount(data.likes);
            });

        });

}

// --- Supprimer son propre post ---

function deletePost(postId, button) {

    if (!confirm("Supprimer définitivement cette publication ?")) return;

    button.disabled = true;

    fetch("/api/delete_post/" + postId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (!data.success) {
                button.disabled = false;
                return;
            }

            const card = document.querySelector(`[data-post-id="${postId}"]`);
            if (card) card.remove();

        })

        .catch(() => { button.disabled = false; });

}

// --- Sauvegarder (playlist) ---

function savePost(postId, button) {

    button.classList.add("save-animation");
    setTimeout(() => button.classList.remove("save-animation"), 400);

    fetch("/api/save/" + postId, { method: "POST" })

        .then(r => r.json())

        .then(data => {

            if (!data.success) return;

            document.querySelectorAll(`[data-save-btn][onclick*="savePost(${postId},"]`).forEach(btn => {
                btn.dataset.saved = data.saved ? "1" : "0";
                btn.classList.toggle("saved", data.saved);
            });

            showToast(data.saved ? "Ajouté à ta playlist" : "Retiré de ta playlist");

        });

}

// --- Partage ---

function setupShare() {

    document.querySelectorAll("[data-share-btn]").forEach(btn => {

        btn.addEventListener("click", async () => {

            const postId = btn.dataset.postId;
            const url = window.location.origin + "/post/" + postId;

            if (navigator.share) {

                try {
                    await navigator.share({
                        title: "Kayli Quest",
                        text: "Regarde cette quête sur Kayli Quest !",
                        url: url
                    });
                } catch (err) {}

            } else {

                try {
                    await navigator.clipboard.writeText(url);
                    showToast("Lien copié !");
                } catch (err) {
                    showToast("Impossible de copier le lien");
                }

            }

        });

    });

}

function showToast(message) {

    const toast = document.createElement("div");
    toast.className = "kq-toast";
    toast.textContent = message;

    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add("show"));

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 1800);

}

// --- Légende "voir plus" ---

function setupCaptionToggle() {

    document.querySelectorAll("[data-caption]").forEach(caption => {

        if (caption.textContent.trim().length <= 90) return;

        caption.classList.add("truncated");

        caption.addEventListener("click", () => {
            caption.classList.toggle("truncated");
        });

    });

}

// --- Vue (une fois par post) ---

const viewedPosts = new Set();

function markViewed(postId) {

    if (!postId || viewedPosts.has(postId)) return;
    viewedPosts.add(postId);

    fetch("/api/view/" + postId, { method: "POST" }).catch(() => {});

}

// --- Formatage des compteurs (1.2K, 3.4M) ---

function formatCount(n) {

    n = parseInt(n, 10) || 0;

    if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "K";

    return String(n);

}
