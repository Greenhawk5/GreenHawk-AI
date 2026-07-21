// Before/after comparison viewer — pointer drag, keyboard, zoom, fullscreen.

let state = {
  images: { original: null, zhang: null, deoldify: null, flux: null },
  left: "original",
  right: "flux",
  pos: 50,   // %
  zoom: 1,
};

function el(id) { return document.getElementById(id); }

function isRtl() {
  return document.documentElement.getAttribute("dir") === "rtl";
}

export function setResults({ original, zhang, deoldify, flux }) {
  state.images = { original, zhang, deoldify, flux };
  const available = Object.entries(state.images)
    .filter(([, url]) => Boolean(url))
    .map(([key]) => key);
  const preferredRight = ["flux", "deoldify", "zhang", "original"].find((key) => state.images[key]);

  state.left = state.images.original ? "original" : available[0];
  state.right = preferredRight;
  if (state.right === state.left && available.length > 1) {
    state.right = available.find((key) => key !== state.left);
  }

  ["cmp-select-left", "cmp-select-right"].forEach((id) => {
    const select = el(id);
    if (!select) return;
    Array.from(select.options).forEach((option) => {
      option.disabled = !state.images[option.value];
    });
    select.value = id === "cmp-select-left" ? state.left : state.right;
  });

  el("compare-section")?.classList.remove("hidden");
  el("compare-empty")?.classList.add("hidden");
  el("compare-viewer")?.classList.remove("hidden");
  updateImages();
  document.getElementById("compare-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateImages() {
  const l = state.images[state.left];
  const r = state.images[state.right];
  const imgL = el("cmp-left");
  const imgR = el("cmp-right");
  if (imgL && l) imgL.src = l;
  if (imgR && r) imgR.src = r;
  updateMeta();
}

function setPos(pct) {
  state.pos = Math.max(0, Math.min(100, pct));
  const top = el("cmp-top");
  const div = el("cmp-divider");
  const hnd = el("cmp-handle");

  if (top) {
    top.style.clipPath = `inset(0 ${100 - state.pos}% 0 0)`;
  }
  if (div) {
    div.style.left = `${state.pos}%`;
  }
  if (hnd) {
    hnd.style.left = `${state.pos}%`;
    hnd.setAttribute("aria-valuenow", String(Math.round(state.pos)));
  }
  const posEl = el("cmp-pos"); if (posEl) posEl.textContent = Math.round(state.pos) + "%";
}

function setZoom(z) {
  state.zoom = Math.max(1, Math.min(4, z));
  document.querySelectorAll(".viewer img").forEach((im) => { im.style.transform = `scale(${state.zoom})`; });
  const zEl = el("cmp-zoom"); if (zEl) zEl.textContent = state.zoom.toFixed(2) + "×";
}

function updateMeta() {
  const imgL = el("cmp-left");
  const dimEl = el("cmp-dim");
  if (imgL && dimEl) {
    imgL.addEventListener("load", () => { dimEl.textContent = `${imgL.naturalWidth}×${imgL.naturalHeight}`; }, { once: true });
  }
  el("cmp-tag-left").textContent = state.left.toUpperCase();
  el("cmp-tag-right").textContent = state.right.toUpperCase();
}

export function initComparison() {
  const viewer = el("compare-viewer");
  const handle = el("cmp-handle");
  const selL = el("cmp-select-left");
  const selR = el("cmp-select-right");
  if (!viewer || !handle) return;

  selL?.addEventListener("change", (e) => { state.left = e.target.value; updateImages(); });
  selR?.addEventListener("change", (e) => { state.right = e.target.value; updateImages(); });

  let dragging = false;
  const setFromEvent = (e) => {
    const rect = viewer.getBoundingClientRect();
    const x = e.clientX - rect.left;
    setPos((x / rect.width) * 100);
  };
  const onDown = (e) => { dragging = true; handle.setPointerCapture?.(e.pointerId); setFromEvent(e); };
  const onMove = (e) => { if (dragging) setFromEvent(e); };
  const onUp = () => { dragging = false; };

  handle.addEventListener("pointerdown", onDown);
  viewer.addEventListener("pointerdown", (e) => { if (e.target === viewer || e.target.tagName === "IMG" || e.target.classList.contains("imgwrap")) { dragging = true; setFromEvent(e); } });
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);

  handle.addEventListener("keydown", (e) => {
    const step = e.shiftKey ? 10 : 2;
    if (e.key === "ArrowLeft")  { e.preventDefault(); setPos(state.pos - step); }
    if (e.key === "ArrowRight") { e.preventDefault(); setPos(state.pos + step); }
    if (e.key === "Home") { e.preventDefault(); setPos(0); }
    if (e.key === "End")  { e.preventDefault(); setPos(100); }
  });

  el("cmp-zoom-in")?.addEventListener("click", () => setZoom(state.zoom + 0.25));
  el("cmp-zoom-out")?.addEventListener("click", () => setZoom(state.zoom - 0.25));
  viewer.addEventListener("wheel", (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    e.preventDefault();
    setZoom(state.zoom + (e.deltaY < 0 ? 0.15 : -0.15));
  }, { passive: false });

  el("cmp-fullscreen")?.addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else viewer.requestFullscreen?.();
  });

  el("cmp-download")?.addEventListener("click", () => {
    const src = state.images[state.right];
    if (!src) return;
    const a = document.createElement("a");
    a.href = src;
    a.download = `greenhawk-${state.right}.jpg`;
    a.rel = "noopener";
    document.body.appendChild(a); a.click(); a.remove();
  });

  document.addEventListener("greenhawk:langchange", () => setPos(state.pos));

  setPos(50);
  setZoom(1);
}
