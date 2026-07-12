// =========================================
// KAYLI QUEST - FEED
// =========================================

document.addEventListener("DOMContentLoaded", () => {
    setupVideoAutoplay();
    setupTapToPause();
    setupDoubleTapLike();
    setupShare();
    setupCaptionToggle();
});

// --- Lecture vidéo uniquement quand visible ---

function setupVideoAutoplay() {

    const videos = document.querySelectorAll("video[data-video]");

    if (!videos.length) return;

    const observer = new IntersectionObserver((entries) => {

        entries.forEach(entry => {

            const video = entry.target;

            if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
                video.play().catch(() => {});
                video.closest(".post").classList.add("in-view");
                markViewed(video.closest(".post").dataset.postId);
            } else {
                video.pause();
                video.closest(".post").classList.remove("in-view");
            }

        });

    }, { threshold: [0, 0.6, 1] });

    videos.forEach(v => observer.observe(v));
}

// --- Tap simple = pause / lecture ---

function setupTapToPause() {

    document.querySelectorAll(".media-wrapper").forEach(wrapper => {

        const video = wrapper.querySelector("video[data-video]");
        if (!video) return;

        const indicator = wrapper.querySelector(".play-indicator");

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

// --- Double-tap = like avec animation de coeur ---

function setupDoubleTapLike() {

    document.querySelectorAll(".post").forEach(post => {

        const wrapper = post.querySelector(".media-wrapper");
        const burst = post.querySelector(".heart-burst");
        const postId = post.dataset.postId;

        let lastTap = 0;

        wrapper.addEventListener("click", (e) => {

            const now = Date.now();

            if (now - lastTap < 300) {

                triggerHeartBurst(burst, e);

                const likeBtn = post.querySelector("[data-like-btn]");
                likePost(postId, likeBtn, true);

            }

            lastTap = now;

        });

    });
}

function triggerHeartBurst(burst, e) {

    burst.classList.remove("burst");
    void burst.offsetWidth; // reset animation
    burst.classList.add("burst");

    setTimeout(() => burst.classList.remove("burst"), 700);
}

// --- Like (utilisé par tap simple sur le bouton et double-tap) ---

function likePost(postId, button, forceLike) {

    button.classList.add("like-animation");

    setTimeout(() => {
        button.classList.remove("like-animation");
    }, 400);

    fetch("/api/like/" + postId)

        .then(r => r.json())

        .then(data => {

            if (data.success) {

                const span = document.getElementById("likes-" + postId);
                span.dataset.count = data.likes;
                span.textContent = formatCount(data.likes);

            }

        });

}

// --- Partage ---

function setupShare() {

    document.querySelectorAll("[data-share-btn]").forEach(btn => {

        btn.addEventListener("click", async (e) => {

            e.stopPropagation();

            const postId = btn.dataset.postId;
            const url = window.location.origin + "/post/" + postId;

            if (navigator.share) {

                try {
                    await navigator.share({
                        title: "Kayli Quest",
                        text: "Regarde cette quête sur Kayli Quest !",
                        url: url
                    });
                } catch (err) {
                    // annulé par l'utilisateur, rien à faire
                }

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

        if (caption.textContent.trim().length <= 70) return;

        caption.classList.add("truncated");

        caption.addEventListener("click", () => {
            caption.classList.toggle("truncated");
        });

    });

}

// --- Marquer une vue (une fois par post, par session navigateur) ---

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
