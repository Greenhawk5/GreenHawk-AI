// Upload workspace — drag/drop, file picker, preview, validation.
import { startColorize } from "./api.js";
import { startJob } from "./jobs.js";
import { t } from "./language.js";

const MAX_BYTES = 20 * 1024 * 1024;
const ACCEPT = ["image/jpeg", "image/png", "image/webp"];

function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

function validate(file) {
  if (!file) return "No file selected.";
  if (!ACCEPT.includes(file.type)) return "Unsupported format. Use JPG, PNG, or WEBP.";
  if (file.size > MAX_BYTES) return "File is larger than 20 MB.";
  return null;
}

let currentFile = null;
let originalPreviewUrl = null;

export function initUpload() {
  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("file-input");
  const preview = document.getElementById("upload-preview");
  const previewImg = document.getElementById("preview-img");
  const fileName = document.getElementById("file-name");
  const fileSize = document.getElementById("file-size");
  const fileType = document.getElementById("file-type");
  const startBtn = document.getElementById("start-btn");
  const replaceBtn = document.getElementById("replace-btn");
  const errorBox = document.getElementById("upload-error");
  if (!dropzone) return;

  function setError(msg, { retry = false } = {}) {
    if (!errorBox) return;
    errorBox.replaceChildren();
    if (!msg) {
      errorBox.classList.add("hidden");
      return;
    }

    const message = document.createElement("span");
    message.textContent = msg;
    errorBox.appendChild(message);
    if (retry) {
      const retryButton = document.createElement("button");
      retryButton.type = "button";
      retryButton.className = "btn btn-ghost";
      retryButton.textContent = t("pipeline.retry");
      retryButton.addEventListener("click", submitUpload);
      errorBox.appendChild(retryButton);
    }
    errorBox.classList.remove("hidden");
  }

  function selectFile(file) {
    setError(null);
    const err = validate(file);
    if (err) { setError(err); return; }
    currentFile = file;
    if (originalPreviewUrl) URL.revokeObjectURL(originalPreviewUrl);
    originalPreviewUrl = URL.createObjectURL(file);
    previewImg.src = originalPreviewUrl;
    fileName.textContent = file.name;
    fileSize.textContent = fmtBytes(file.size);
    fileType.textContent = file.type.replace("image/", "").toUpperCase();
    preview.classList.remove("hidden");
    dropzone.classList.add("hidden");
    window.__greenhawk_originalUrl = originalPreviewUrl;
  }

  dropzone.addEventListener("click", () => input.click());
  dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
  ["dragenter", "dragover"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove("drag"); }));
  dropzone.addEventListener("drop", (e) => { const f = e.dataTransfer.files?.[0]; if (f) selectFile(f); });
  input.addEventListener("change", (e) => { const f = e.target.files?.[0]; if (f) selectFile(f); });

  replaceBtn?.addEventListener("click", () => {
    preview.classList.add("hidden");
    dropzone.classList.remove("hidden");
    input.value = "";
    currentFile = null;
    setError(null);
  });

  async function submitUpload() {
    if (!currentFile) return;
    setError(null);
    startBtn.disabled = true;
    startBtn.textContent = "…";
    try {
      console.group("[GreenHawk Upload Debug]");
      console.log("Starting colorization for file:", currentFile.name, currentFile.type, currentFile.size);
      const res = await startColorize(currentFile);
      console.log("Colorize API response:", res);
      console.log("Returned job_id:", res?.job_id);
      console.log("Returned input image:", res?.input_image);
      console.groupEnd();

      if (!res?.job_id) throw new Error("Backend did not return a job_id.");
      console.log("[GreenHawk Upload Debug] Starting job polling:", res.job_id);
      startJob(res.job_id, {
        localOriginalUrl: originalPreviewUrl,
        inputImage: res.input_image,
        retry: () => startBtn.click(),
      });
      // Scroll to pipeline
      document.getElementById("pipeline")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      console.error("[GreenHawk Upload Debug] Upload failed:", err);
      setError(err.message || "Something went wrong.", { retry: true });
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = t("upload.start");
    }
  }

  startBtn?.addEventListener("click", submitUpload);
}
