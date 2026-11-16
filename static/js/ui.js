// Small UI helpers: scroll-reveal animations and auto-hiding toasts.
(function () {
    const selector = [
        ".blog-card", ".feature-card", ".section-heading", ".post-card",
        ".trend-item", ".stat-card", ".comment-card", ".category-chip",
    ].join(",");

    function reveal() {
        const items = document.querySelectorAll(selector);
        if (!("IntersectionObserver" in window)) return;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    el.classList.add("is-visible");
                    // drop the stagger delay so hover effects stay instant
                    setTimeout(() => { el.style.transitionDelay = ""; }, 700);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08 });
        items.forEach((el, i) => {
            if (el.classList.contains("reveal")) return;
            el.classList.add("reveal");
            el.style.transitionDelay = `${Math.min(i % 6, 5) * 60}ms`;
            observer.observe(el);
        });
    }

    function toasts() {
        document.querySelectorAll(".toast").forEach((toast) => {
            setTimeout(() => {
                toast.style.transition = "opacity .4s";
                toast.style.opacity = "0";
                setTimeout(() => toast.remove(), 450);
            }, 4500);
        });
    }

    document.addEventListener("DOMContentLoaded", () => { reveal(); toasts(); });
    // Infinite scroll adds cards later; animate those too.
    new MutationObserver(reveal).observe(document.documentElement, { childList: true, subtree: true });
})();
