// GreenHawk AI — page bootstrap: nav, mobile menu, FAQ, history, module init.
import { initTheme } from "./theme.js";
import { initLanguage, t } from "./language.js";
import { initUpload } from "./upload.js";
import { initJobs } from "./jobs.js";
import { initComparison, setResults } from "./comparison.js";
import { initDownloads, setDownloads } from "./download.js";

function initNav() {
  const nav = document.querySelector(".nav");
  const onScroll = () => nav?.classList.toggle("scrolled", window.scrollY > 6);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const burger = document.querySelector("[data-hamburger]");
  const panel = document.getElementById("mobile-panel");
  const backdrop = document.getElementById("mobile-backdrop");
  const close = () => { panel?.classList.remove("open"); backdrop?.classList.remove("open"); burger?.setAttribute("aria-expanded", "false"); };
  const open = () => { panel?.classList.add("open"); backdrop?.classList.add("open"); burger?.setAttribute("aria-expanded", "true"); };
  burger?.addEventListener("click", () => {
    (panel?.classList.contains("open") ? close : open)();
  });
  backdrop?.addEventListener("click", close);
  panel?.querySelectorAll("a").forEach((a) => a.addEventListener("click", close));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
}

function initFAQ() {
  document.querySelectorAll(".faq-item").forEach((item) => {
    const q = item.querySelector(".faq-q");
    q?.addEventListener("click", () => {
      const open = item.getAttribute("data-open") === "true";
      item.setAttribute("data-open", open ? "false" : "true");
      q.setAttribute("aria-expanded", open ? "false" : "true");
    });
  });
}

const HKEY = "greenhawk.history";
const HMAX = 8;
const H_EXPIRY_DAYS = 30;

// Filter out expired items when loading history
function filterExpired(history) {
  const now = Date.now();
  return history.filter(item => {
    if (!item.at) return true;
    const ageDays = (now - item.at) / (1000 * 60 * 60 * 24);
    return ageDays <= H_EXPIRY_DAYS;
  });
}

export function pushHistory(entry) {
  try {
    let arr = JSON.parse(localStorage.getItem(HKEY) || "[]");
    arr = filterExpired(arr);
    arr.unshift(entry);
    localStorage.setItem(HKEY, JSON.stringify(arr.slice(0, HMAX)));
    renderHistory();
  } catch {}
}

function renderHistory() {
  const grid = document.getElementById("history-grid");
  const empty = document.getElementById("history-empty");
  if (!grid) return;
  let arr = [];
  try { arr = JSON.parse(localStorage.getItem(HKEY) || "[]"); } catch {}
  // Filter expired items during rendering
  arr = filterExpired(arr);
  grid.innerHTML = "";
  if (!arr.length) { empty?.classList.remove("hidden"); grid.classList.add("hidden"); return; }
  empty?.classList.add("hidden"); grid.classList.remove("hidden");
  arr.forEach((it) => {
    const el = document.createElement("article");
    el.className = "history-item";
    const d = new Date(it.at || Date.now());
    const models = Array.isArray(it.models) && it.models.length ? it.models : ["Zhang", "DeOldify", "FLUX"];
    const chips = models.map((m) => `<span class="h-chip">${m}</span>`).join("");
    el.innerHTML = `
      <a class="h-thumb" href="#compare-section" data-history-open aria-label="Open result">
        <img src="${it.thumb}" alt="Previous colorization" loading="lazy" />
      </a>
      <div class="h-body">
        <div class="h-date">${d.toLocaleDateString()} · ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
        <div class="h-models" aria-label="${t("history.card.models")}">${chips}</div>
        <a class="h-open" href="#compare-section" data-history-open>${t("history.card.open")} →</a>
      </div>`;
    grid.appendChild(el);
    // Attach event listener INSIDE the loop to ensure proper closure
    el.querySelectorAll("[data-history-open]").forEach((link) => {
      link.addEventListener("click", (event) => openHistory(it, event));
    });
  });
}

function openHistory(entry, event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  // Validate images entry
  if (!entry.images || typeof entry.images !== 'object') {
    console.error("Invalid history entry: missing images", entry);
    return;
  }

  const images = entry.images;
  
  // Check if any valid image exists
  const hasValidImage = Object.values(images).some(url => url && typeof url === 'string' && url.trim() !== '');
  
  if (!hasValidImage) {
    console.error("No valid images in history entry", entry);
    // Show a user-friendly message instead of doing nothing
    const errBox = document.getElementById("pipe-error");
    if (errBox) {
      errBox.classList.remove("hidden");
      errBox.querySelector("[data-msg]").textContent = t("history.error.unavailable") || "This colorization is no longer available";
      const retryBtn = errBox.querySelector("button");
      if (retryBtn) retryBtn.style.display = 'none';
    }
    return;
  }

  // Update comparison viewer
  setResults(images);
  // Update download cards
  setDownloads(images);
  
  // Scroll to comparison section
  const compareSection = document.getElementById("compare-section");
  if (compareSection) {
    compareSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function markActiveNav() {
  const path = location.pathname.replace(/\/+$/, "");
  document.querySelectorAll("[data-nav-link]").forEach((a) => {
    const href = new URL(a.getAttribute("href"), location.href).pathname.replace(/\/+$/, "");
    if (href === path || (path === "" && href.endsWith("/index.html")) || (path.endsWith("/index.html") && href.endsWith("/index.html"))) {
      a.classList.add("active");
    }
  });
}

function initScrollToTop() {
  const scrollTopBtn = document.querySelector("[data-scroll-top]");

  if (!scrollTopBtn) return;

  const scrollThreshold = 300;

  function updateVisibility() {
    if (window.scrollY > scrollThreshold) {
      scrollTopBtn.style.display = "inline-flex";
      requestAnimationFrame(() => {
        scrollTopBtn.classList.add("visible");
      });
    } else {
      scrollTopBtn.classList.remove("visible");
      requestAnimationFrame(() => {
        scrollTopBtn.style.display = "none";
      });
    }
  }

  window.addEventListener("scroll", () => {
    requestAnimationFrame(updateVisibility);
  }, { passive: true });

  function scrollToTop() {
    const shouldScrollToUpload = location.pathname === "/index.html" || location.pathname.endsWith("/index.html");

    if (shouldScrollToUpload) {
      const uploadSection = document.getElementById("upload");
      if (uploadSection) {
        uploadSection.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  scrollTopBtn.addEventListener("click", scrollToTop);
}

document.addEventListener("DOMContentLoaded", () => {
  // Global error listeners
  window.addEventListener("error", (event) => {
    console.error("[GreenHawk Global Error]", event.error || event.message);
  });

  window.addEventListener("unhandledrejection", (event) => {
    console.error("[GreenHawk Promise Rejection]", event.reason);
  });

  initTheme();
  initLanguage();
  initNav();
  initFAQ();
  markActiveNav();
  initScrollToTop();
  // Home-only modules
  if (document.getElementById("dropzone")) initUpload();
  if (document.getElementById("pipeline")) initJobs();
  if (document.getElementById("compare-viewer")) initComparison();
  if (document.getElementById("downloads-section")) initDownloads();
  if (document.getElementById("history-grid")) renderHistory();
});
