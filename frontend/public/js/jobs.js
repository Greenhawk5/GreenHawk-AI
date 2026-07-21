// Job polling drives the existing pipeline, comparison, and downloads UI.
import { absolutize, pollJob, resultUrl } from "./api.js";
import { setResults } from "./comparison.js";
import { setDownloads } from "./download.js";
import { pushHistory } from "./main.js";
import { t } from "./language.js";

let controller = null;
let lastRetry = null;

export function startJob(jobId, opts = {}) {
  console.log("[GreenHawk Jobs Debug] startJob called:", jobId);
  if (controller) controller.abort();
  controller = new AbortController();
  lastRetry = opts.retry || null;

  const els = ui();
  showPipeline();
  setStatus("queued", 0);
  clearError();
  els.stages.forEach((stage) => stage.classList.remove("active", "done"));

  pollJob(jobId, {
    intervalMs: 2000,
    signal: controller.signal,
    onUpdate: (job) => {
      console.group("[GreenHawk Jobs Debug] onUpdate");
      console.log("Received job object:", job);
      console.log("Job status:", job?.status);
      console.log("Job progress:", job?.progress);
      console.groupEnd();
      renderJob(job, opts);
    },
  }).catch((error) => {
    if (error.name !== "AbortError") renderError(error.message || "Colorization failed.");
  });
}

function ui() {
  return {
    section: document.getElementById("pipeline"),
    badge: document.getElementById("pipe-badge"),
    bar: document.getElementById("pipe-bar"),
    num: document.getElementById("pipe-num"),
    progress: document.querySelector("#pipeline .progress"),
    stages: Array.from(document.querySelectorAll("[data-stage]")),
    err: document.getElementById("pipe-error"),
  };
}

function showPipeline() { ui().section?.classList.remove("hidden"); }

function setStatus(status, progress) {
  const { badge, bar, num, progress: progressBar, stages } = ui();
  if (badge) {
    badge.setAttribute("data-status", status);
    const key = `pipeline.status.${status}`;
    badge.querySelector("[data-label]").textContent = t(key);
  }

  const pct = Math.max(0, Math.min(100, Number(progress) || 0));
  if (bar) bar.style.width = `${pct}%`;
  if (num) num.textContent = `${pct}%`;
  progressBar?.setAttribute("aria-valuenow", String(pct));

  const stage = Object.fromEntries(stages.map((element) => [element.dataset.stage, element]));
  Object.values(stage).forEach((element) => element.classList.remove("active", "done"));

  if (status === "queued") {
    stage.prep?.classList.add("active");
    return;
  }

  stage.prep?.classList.add("done");
  if (pct < 40) {
    stage.zhang?.classList.add("active");
  } else if (pct < 70) {
    stage.zhang?.classList.add("done");
    stage.deoldify?.classList.add("active");
  } else if (pct < 95) {
    stage.zhang?.classList.add("done");
    stage.deoldify?.classList.add("done");
    stage.flux?.classList.add("active");
  } else {
    ["zhang", "deoldify", "flux"].forEach((key) => stage[key]?.classList.add("done"));
    if (status === "completed") stage.done?.classList.add("done");
    else if (status === "processing") stage.done?.classList.add("active");
  }
}

function renderJob(job, opts) {
  console.group("[GreenHawk Render Debug]");
  console.log("renderJob received:", job);
  console.log("Job status:", job?.status);
  console.log("Job results:", job?.results);
  console.groupEnd();

  // debugger;

  console.log("JOB RESPONSE:", job);

  clearError();
  setStatus(job.status, job.progress ?? 0);

  if (job.status === "completed" && job.results) {

    console.log("[GreenHawk Render Debug] Checking completion state");
    console.log("[GreenHawk Render Debug] Completed job detected");
    console.log("Input image:", job.input_image);
    console.log("Model results:", job.results);

    const original = absolutize(job.input_image) || opts.localOriginalUrl;
    const zhang = resultUrl(job.results.zhang);
    const deoldify = resultUrl(job.results.deoldify);
    const flux = resultUrl(job.results.flux);
    setResults({ original, zhang, deoldify, flux });
    setDownloads({ original, zhang, deoldify, flux });
    pushHistory({
      jobId: job.job_id,
      at: Date.now(),
      thumb: flux || deoldify || zhang || original,
      models: [zhang && "Zhang", deoldify && "DeOldify", flux && "FLUX"].filter(Boolean),
      images: { original, zhang, deoldify, flux },
    });
  } else if (job.status === "failed") {
    renderError(job.error || t("pipeline.error"));
  }
}

function renderError(message) {
  const { err } = ui();
  if (!err) return;
  err.classList.remove("hidden");
  err.querySelector("[data-msg]").textContent = message;
}

function clearError() { ui().err?.classList.add("hidden"); }

export function initJobs() {
  document.getElementById("pipe-retry")?.addEventListener("click", () => {
    if (lastRetry) lastRetry();
  });
}
