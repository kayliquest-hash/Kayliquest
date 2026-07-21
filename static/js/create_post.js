// =========================================
// KAYLI QUEST - CRÉATION DE POST
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    const fileInput = document.getElementById("media");
    const uploadCard = document.getElementById("upload-card");
    const previewWrapper = document.getElementById("preview-wrapper");
    const previewImg = document.getElementById("preview-img");
    const previewVideo = document.getElementById("preview-video");
    const removeBtn = document.getElementById("preview-remove");
    const descriptionInput = document.getElementById("description");
    const charCount = document.getElementById("char-count");
    const form = document.getElementById("create-form");
    const publishBtn = document.getElementById("publish-btn");

    const MAX_SIZE_MB = 50;

    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];
        if (!file) return;

        if (file.size > MAX_SIZE_MB * 1024 * 1024) {
            alert("Le fichier est trop lourd (max " + MAX_SIZE_MB + " Mo).");
            fileInput.value = "";
            return;
        }

        const url = URL.createObjectURL(file);

        if (file.type.startsWith("video/")) {

            previewVideo.src = url;
            previewVideo.style.display = "block";
            previewImg.style.display = "none";

        } else {

            previewImg.src = url;
            previewImg.style.display = "block";
            previewVideo.style.display = "none";

        }

        uploadCard.style.display = "none";
        previewWrapper.style.display = "block";

    });

    removeBtn.addEventListener("click", () => {

        fileInput.value = "";
        previewWrapper.style.display = "none";
        uploadCard.style.display = "flex";
        previewImg.src = "";
        previewVideo.src = "";

    });

    descriptionInput.addEventListener("input", () => {
        charCount.textContent = descriptionInput.value.length;
    });

    const tagToggleBtn = document.getElementById("tag-toggle-btn");
    const tagList = document.getElementById("tag-list");
    const tagCountBadge = document.getElementById("tag-count-badge");

    if (tagToggleBtn) {

        tagToggleBtn.addEventListener("click", () => {
            tagList.hidden = !tagList.hidden;
        });

        tagList.addEventListener("change", () => {

            const checked = tagList.querySelectorAll("input:checked").length;
            tagCountBadge.textContent = checked > 0 ? checked : "";

        });

    }

    form.addEventListener("submit", () => {

        publishBtn.disabled = true;
        publishBtn.innerHTML = "<span class=\"spinner\"></span> Publication en cours...";

    });

});
