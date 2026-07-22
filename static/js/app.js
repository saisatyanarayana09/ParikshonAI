document.addEventListener("DOMContentLoaded", () => {
    setupTheme();
    setupMenu();
    setupUploads();
    setupForms();
    setupCopyButtons();
    setupSuggestions();
    setupKeywordFilter();
    setupTextSearch();
    setupRegenerate();
    setupChatScroll();
});

function setupTheme() {
    const saved = localStorage.getItem("parikshon-theme");
    if (saved) document.documentElement.dataset.theme = saved;

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const current = document.documentElement.dataset.theme === "light" ? "dark" : "light";
            document.documentElement.dataset.theme = current;
            localStorage.setItem("parikshon-theme", current);
        });
    });
}

function setupMenu() {
    const toggle = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("#primary-menu");
    if (!toggle || !menu) return;

    toggle.addEventListener("click", () => {
        const open = menu.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
    });
}

function setupUploads() {
    document.querySelectorAll("[data-upload-zone]").forEach((zone) => {
        const input = zone.querySelector("input[type='file']");
        const bar = zone.querySelector(".progress-bar");
        // Model 2: placeholder text lives in .bar-placeholder-text
        const meta = zone.querySelector(".bar-placeholder-text") || zone.querySelector("[data-file-meta]");
        const formEl = zone.closest("form");
        if (!input) return;

        // Drag events on the outer form (the pill-shaped bar)
        const dragTarget = formEl || zone;
        ["dragenter", "dragover"].forEach((eventName) => {
            dragTarget.addEventListener(eventName, (event) => {
                event.preventDefault();
                dragTarget.classList.add("drag-over");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            dragTarget.addEventListener(eventName, (event) => {
                event.preventDefault();
                dragTarget.classList.remove("drag-over");
            });
        });

        dragTarget.addEventListener("drop", (event) => {
            const files = event.dataTransfer.files;
            if (files.length) {
                input.files = files;
                updateFileMeta(input, meta);
                animateProgress(zone, bar, 100);
            }
        });

        input.addEventListener("change", () => {
            updateFileMeta(input, meta);
            animateProgress(zone, bar, input.files.length ? 100 : 0);
            // Auto-submit on file select for the upload bar
            if (input.files.length && formEl) {
                // Small delay so the label text updates first
                window.setTimeout(() => formEl.requestSubmit(), 120);
            }
        });
    });
}

function setupForms() {
    document.querySelectorAll(".ai-form").forEach((form) => {
        form.addEventListener("submit", () => {
            form.classList.add("processing");
            const button = form.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = "Processing...";
            }
            const zone = form.querySelector("[data-upload-zone]");
            if (zone) runProcessingStages(zone);
        });
    });
}

function updateFileMeta(input, meta) {
    if (!meta) return;
    const file = input.files && input.files[0];
    if (!file) {
        meta.textContent = "Attach a document — PDF, DOCX, PNG…";
        return;
    }
    meta.textContent = `${file.name}  ·  ${formatBytes(file.size)}`;
}

function formatBytes(bytes) {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, power)).toFixed(power ? 1 : 0)} ${units[power]}`;
}

function animateProgress(zone, bar, target) {
    if (!bar) return;
    bar.style.width = `${target}%`;
    const progress = zone.querySelector(".upload-progress");
    if (progress) progress.setAttribute("aria-valuenow", String(target));
}

function runProcessingStages(zone) {
    const steps = Array.from(zone.querySelectorAll("[data-processing-steps] li"));
    if (!steps.length) return;
    steps.forEach((step) => step.classList.remove("active", "done"));
    steps.forEach((step, index) => {
        window.setTimeout(() => {
            steps.slice(0, index).forEach((item) => item.classList.add("done"));
            step.classList.add("active");
        }, index * 520);
    });
}

function setupCopyButtons() {
    document.querySelectorAll("[data-copy-target]").forEach((button) => {
        button.addEventListener("click", async () => {
            const target = document.querySelector(button.dataset.copyTarget);
            if (!target) return;
            await navigator.clipboard.writeText(target.innerText);
            flashButton(button, "Copied");
        });
    });

    document.querySelectorAll("[data-copy-nearest]").forEach((button) => {
        button.addEventListener("click", async () => {
            const bubble = button.closest(".chat-bubble");
            if (!bubble) return;
            await navigator.clipboard.writeText(bubble.innerText);
            flashButton(button, "Copied");
        });
    });
}

function setupSuggestions() {
    document.querySelectorAll("[data-fill-question], .suggestion-chip").forEach((button) => {
        button.addEventListener("click", () => {
            // Find the nearest form or the question form on the page
            const form = button.closest("form") || document.getElementById("question-form");
            const textarea = form && (form.querySelector("textarea") || form.querySelector("input[name='question']"));
            if (!textarea) return;
            textarea.value = button.dataset.fillQuestion || button.textContent.trim();
            textarea.focus();
        });
    });
}

function setupKeywordFilter() {
    const input = document.querySelector("[data-filter-keywords]");
    if (!input) return;
    input.addEventListener("input", () => {
        const value = input.value.trim().toLowerCase();
        document.querySelectorAll("[data-keyword-chip]").forEach((chip) => {
            chip.hidden = value && !chip.textContent.toLowerCase().includes(value);
        });
    });
}

function setupTextSearch() {
    document.querySelectorAll("[data-filter-text]").forEach((input) => {
        input.addEventListener("input", () => {
            const target = document.querySelector(input.dataset.filterText);
            if (!target) return;
            const value = input.value.trim().toLowerCase();
            target.style.boxShadow = value && target.innerText.toLowerCase().includes(value)
                ? "0 0 0 2px rgba(128, 216, 255, 0.42)"
                : "";
        });
    });
}

function setupRegenerate() {
    document.querySelectorAll("[data-regenerate]").forEach((button) => {
        button.addEventListener("click", () => {
            const form = document.querySelector(".ai-form");
            if (form) form.requestSubmit();
        });
    });
}

function setupChatScroll() {
    // Scroll both the old chat-history and the new chat-messages-area to bottom
    document.querySelectorAll(".chat-history, .chat-messages-area").forEach((el) => {
        el.scrollTop = el.scrollHeight;
    });
}

function flashButton(button, label) {
    const previous = button.textContent;
    button.textContent = label;
    window.setTimeout(() => {
        button.textContent = previous;
    }, 1200);
}
