document.addEventListener("DOMContentLoaded", () => {
    setupTheme();
    setupMenu();
    setupSidebarToggle();
    setupUploads();
    setupForms();
    setupCopyButtons();
    setupSuggestions();
    setupKeywordFilter();
    setupTextSearch();
    setupRegenerate();
    setupChatScroll();
    setupChatKeyboard();
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

    // Close on outside click
    document.addEventListener("click", (e) => {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
            menu.classList.remove("open");
            toggle.setAttribute("aria-expanded", "false");
        }
    });
}

function setupSidebarToggle() {
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.querySelector(".workspace-sidebar");
    if (!toggle || !sidebar) return;

    // Only show toggle on mobile
    const checkMobile = () => {
        toggle.style.display = window.innerWidth <= 768 ? "flex" : "none";
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);

    toggle.addEventListener("click", () => {
        sidebar.classList.toggle("sidebar-open");
    });

    // Close sidebar when clicking a nav item on mobile
    sidebar.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            if (window.innerWidth <= 768) sidebar.classList.remove("sidebar-open");
        });
    });
}

function setupChatKeyboard() {
    const textarea = document.querySelector("#question-form textarea");
    if (!textarea) return;
    textarea.addEventListener("keydown", (e) => {
        // Ctrl+Enter or Cmd+Enter to submit
        if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            const form = textarea.closest("form");
            if (form) submitChatAJAX(form);
        }
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
        form.addEventListener("submit", (e) => {
            if (form.id === "question-form") {
                e.preventDefault();
                submitChatAJAX(form);
                return;
            }

            // For uploads, just show the loading overlay while the page navigates
            form.classList.add("processing");
            const overlay = document.querySelector(".upload-overlay");
            if (overlay) overlay.classList.add("active");
            
            const button = form.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.dataset.originalText = button.textContent;
                button.textContent = "Processing...";
            }
        });
    });

    // Auto dismiss toasts
    setTimeout(() => {
        document.querySelectorAll(".toast-message").forEach(t => {
            t.classList.add("hide");
            setTimeout(() => t.remove(), 400);
        });
    }, 4000);
}

async function submitChatAJAX(form) {
    const input = form.querySelector("input[name='question'], textarea[name='question']");
    const questionText = input.value.trim();
    if (!questionText) return;

    // 1. Add user message to UI
    const chatArea = document.getElementById("chat-messages-area");
    const emptyState = document.querySelector(".chat-empty-state");
    if (emptyState) emptyState.remove();

    chatArea.insertAdjacentHTML("beforeend", `
        <article class="chat-bubble user-bubble">
            <span class="bubble-label">You</span>
            <p>${escapeHTML(questionText)}</p>
        </article>
        <article class="chat-bubble ai-bubble ai-typing">
            <div class="ai-loader" style="display:flex;"><span></span><span></span><span></span></div>
        </article>
    `);
    
    // Clear input & disable form
    input.value = "";
    form.classList.add("processing");
    const submitBtn = form.querySelector("button[type='submit']");
    if(submitBtn) submitBtn.disabled = true;
    chatArea.scrollTop = chatArea.scrollHeight;

    try {
        const formData = new FormData(form);
        formData.set("question", questionText);
        const res = await fetch(form.action || window.location.href, {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });
        const data = await res.json();
        
        // Remove typing indicator
        chatArea.querySelector(".ai-typing")?.remove();

        if (data.success) {
            // Use marked.js if available, otherwise basic formatting
            const renderMarkdown = (text) => {
                if (window.__renderAIAnswer) return window.__renderAIAnswer(text);
                if (window.marked) return window.marked.parse(text);
                return escapeHTML(text).replace(/\n/g, '<br>');
            };

            const bubble = document.createElement('article');
            bubble.className = 'chat-bubble ai-bubble';
            bubble.innerHTML = `
                <span class="bubble-label">Parikshon AI</span>
                <div class="ai-answer-body">${renderMarkdown(data.answer)}</div>
                <div class="message-tools">
                    <button type="button" data-copy-nearest>Copy</button>
                </div>
            `;
            chatArea.appendChild(bubble);
            if (data.limit_reached) {
                location.reload(); // Reload to show the limit banner
            }
        } else {
            alert(data.error || "Failed to get answer");
        }
    } catch (e) {
        chatArea.querySelector(".ai-typing")?.remove();
        alert("A network error occurred. Please try again.");
    }

    form.classList.remove("processing");
    if(submitBtn) submitBtn.disabled = false;
    chatArea.scrollTop = chatArea.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
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
