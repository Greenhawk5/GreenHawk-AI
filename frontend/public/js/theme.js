// Theme toggle — dark (default) / light — persisted to localStorage.
const KEY = "greenhawk.theme";

function apply(theme) {
  const t = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", t);
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(t === "dark"));
    const sun = btn.querySelector("[data-icon='sun']");
    const moon = btn.querySelector("[data-icon='moon']");
    if (sun && moon) {
      sun.style.display = t === "dark" ? "none" : "";
      moon.style.display = t === "dark" ? "" : "none";
    }
  });
  // Swap footer/social icon sources between Dark and Light variants
  document.querySelectorAll("[data-icon-swap]").forEach((img) => {
    const src = t === "dark" ? img.getAttribute("data-icon-dark") : img.getAttribute("data-icon-light");
    if (src) img.setAttribute("src", src);
  });
}

export function initTheme() {
  const stored = localStorage.getItem(KEY);
  const preferred = stored || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  apply(preferred);
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem(KEY, next);
      apply(next);
    });
  });
}
