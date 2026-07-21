// GreenHawk API service layer. This is the single frontend API origin.
export const API_BASE_URL = (
  (typeof window !== "undefined" && window.GREENHAWK_API_BASE) ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

function url(path) {
  return `${API_BASE_URL}${path}`;
}

async function errorMessage(response, fallback) {
  try {
    const body = await response.json();
    const detail = body?.detail || body?.message;
    if (typeof detail === "string") return detail;
    if (detail?.message) return detail.message;
    if (detail?.error) return detail.error;
  } catch {}
  return fallback;
}

/** POST /colorize - multipart/form-data, field name "file". */
export async function startColorize(file) {
  const form = new FormData();
  form.append("file", file);
  let response;
  try {
    response = await fetch(url("/colorize"), { method: "POST", body: form });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(`Could not reach the colorization service at ${API_BASE_URL}. Check that the backend is running and that CORS allows this page.`);
  }
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Upload failed (${response.status})`));
  }
  return response.json();
}

/** GET /jobs/{job_id} - returns the current FastAPI job payload. */
export async function getJob(jobId, { signal } = {}) {
  const response = await fetch(url(`/jobs/${encodeURIComponent(jobId)}`), { signal });
  if (!response.ok) {
    throw new Error(await errorMessage(response, `Job fetch failed (${response.status})`));
  }
  return response.json();
}

/** Poll a job every two seconds until it reaches a terminal state. */
export function pollJob(jobId, { onUpdate, intervalMs = 2000, signal } = {}) {
  return new Promise((resolve, reject) => {
    let stopped = false;
    const stop = () => { stopped = true; };
    if (signal) {
      signal.addEventListener("abort", () => {
        stop();
        reject(new DOMException("Aborted", "AbortError"));
      }, { once: true });
    }

    async function tick() {
      if (stopped) return;
      try {
        const job = await getJob(jobId, { signal });
        if (stopped) return;
        console.group("[GreenHawk Poll Debug]");
        console.log("Job ID:", jobId);
        console.log("Job response:", job);
        console.log("Status:", job?.status);
        console.log("Progress:", job?.progress);
        console.log("Results:", job?.results);
        console.groupEnd();
        onUpdate?.(job);
        if (job.status === "completed" || job.status === "failed") {
          stop();
          resolve(job);
          return;
        }
      } catch (error) {
        if (error.name === "AbortError") return;
        console.error("[GreenHawk Poll Debug] Poll request failed:", error);
        stop();
        reject(error);
        return;
      }
      setTimeout(tick, intervalMs);
    }

    tick();
  });
}

/** Extract an image URL from a model result object. */
export function resultUrl(entry) {
  if (!entry) return null;
  if (typeof entry === "string") return absolutize(entry);
  const candidate = entry.url || entry.image_url || entry.path || entry.file || entry.output || null;
  return candidate ? absolutize(candidate) : null;
}

/** Resolve API-relative file URLs for image and download requests. */
export function absolutize(path) {
  if (!path) return path;
  if (/^https?:\/\//i.test(path) || path.startsWith("data:") || path.startsWith("blob:")) return path;
  return path.startsWith("/") ? `${API_BASE_URL}${path}` : `${API_BASE_URL}/${path}`;
}
