// Per-model downloads plus a client-side ZIP for all available backend files.
import { t } from "./language.js";

const MODELS = [
  { key: "zhang", label: "Zhang" },
  { key: "deoldify", label: "DeOldify" },
  { key: "flux", label: "FLUX" },
];

let urls = { original: null, zhang: null, deoldify: null, flux: null };

export function setDownloads(next) {
  urls = { ...urls, ...next };
  const grid = document.getElementById("dl-grid");
  const section = document.getElementById("downloads-section");
  if (!grid || !section) return;
  section.classList.remove("hidden");
  grid.innerHTML = "";

  MODELS.forEach((model) => {
    const src = urls[model.key];
    if (!src) return;
    const card = document.createElement("div");
    card.className = "card dl-card";
    card.innerHTML = `
      <img src="${src}" alt="${model.label} result" loading="lazy" />
      <div>
        <div class="name">${model.label}</div>
        <div class="fmt">${formatFromUrl(src)}</div>
        <button class="btn btn-ghost" data-dl="${model.key}">${t("downloads.dl")}</button>
      </div>`;
    grid.appendChild(card);
  });

  grid.querySelectorAll("[data-dl]").forEach((button) => {
    button.addEventListener("click", () => downloadOne(button.getAttribute("data-dl")));
  });
}

function extensionFromUrl(src) {
  try {
    const extension = new URL(src, window.location.href).pathname.match(/\.([a-zA-Z0-9]{2,5})$/)?.[1];
    return extension ? `.${extension.toLowerCase()}` : ".jpg";
  } catch {
    return ".jpg";
  }
}

function formatFromUrl(src) {
  return extensionFromUrl(src).slice(1).toUpperCase();
}

async function downloadOne(key) {
  const src = urls[key];
  if (!src) return;
  const name = `greenhawk-${key}${extensionFromUrl(src)}`;
  try {
    const response = await fetch(src);
    if (!response.ok) throw new Error("Download failed");
    trigger(await response.blob(), name);
  } catch {
    const link = document.createElement("a");
    link.href = src;
    link.download = name;
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
}

function trigger(blob, name) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 4000);
}

async function loadJSZip() {
  if (window.JSZip) return window.JSZip;
  await new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js";
    script.onload = resolve;
    script.onerror = () => reject(new Error("Could not load JSZip"));
    document.head.appendChild(script);
  });
  return window.JSZip;
}

async function downloadAll() {
  const files = [
    { key: "original", name: "greenhawk-original" },
    ...MODELS.map(({ key }) => ({ key, name: `greenhawk-${key}` })),
  ].filter(({ key }) => urls[key]);
  if (!files.length) return;

  const button = document.getElementById("dl-all");
  if (button) {
    button.disabled = true;
    button.setAttribute("data-orig", button.textContent);
    button.textContent = "...";
  }

  try {
    const JSZip = await loadJSZip();
    const zip = new JSZip();
    for (const file of files) {
      const response = await fetch(urls[file.key]);
      if (!response.ok) throw new Error(`Could not download ${file.key}.`);
      zip.file(`${file.name}${extensionFromUrl(urls[file.key])}`, await response.blob());
    }
    trigger(await zip.generateAsync({ type: "blob" }), "greenhawk-results.zip");
  } catch (error) {
    alert(error.message || "Could not build ZIP.");
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = button.getAttribute("data-orig") || t("downloads.all");
    }
  }
}

export function initDownloads() {
  document.getElementById("dl-all")?.addEventListener("click", downloadAll);
}
