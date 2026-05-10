const $ = (selector) => document.querySelector(selector);

const state = {
  busy: false,
};

const progressTimers = {};

const progressSteps = {
  index: [
    ["Reading document fields", 20],
    ["Chunking source text", 45],
    ["Writing searchable chunks", 75],
    ["Refreshing source list", 92],
  ],
  upload: [
    ["Reading uploaded file", 25],
    ["Validating UTF-8 text", 45],
    ["Indexing uploaded source", 78],
    ["Refreshing source list", 92],
  ],
  source: [
    ["Contacting source catalog", 35],
    ["Applying latest changes", 70],
    ["Rendering source list", 92],
  ],
  demo: [
    ["Preparing demo knowledge base", 18],
    ["Indexing policy and runbook sources", 45],
    ["Adding sample banking operations notes", 72],
    ["Loading sample questions", 92],
  ],
  ask: [
    ["Guardrail agent scanning request", 14, "guardrail"],
    ["Planner agent preparing workflow", 28, "planner"],
    ["Retriever agent searching citations", 46, "retriever"],
    ["Summarizer agent drafting answer", 64, "summarizer"],
    ["Critic agent checking claims", 82, "critic"],
    ["Judge agent scoring output", 94, "judge"],
  ],
};

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  window.setTimeout(() => el.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function setBusy(isBusy) {
  state.busy = isBusy;
  document.body.classList.toggle("busy", isBusy);
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $("#theme-toggle").textContent = theme === "dark" ? "Light theme" : "Dark theme";
  localStorage.setItem("mak-theme", theme);
}

function setGuide(step) {
  ["source", "ask", "verify"].forEach((name) => {
    $(`#guide-${name}`)?.classList.toggle("active", name === step);
  });
}

function setProgress(id, message, percent, mode = "active") {
  const wrapper = $(`#${id}-progress`);
  const status = $(`#${id}-status`);
  const percentEl = $(`#${id}-percent`);
  const bar = $(`#${id}-bar`);
  if (!wrapper || !status || !percentEl || !bar) return;
  wrapper.classList.toggle("failed", mode === "failed");
  status.textContent = message;
  percentEl.textContent = `${percent}%`;
  bar.style.width = `${percent}%`;
}

function resetAgentSteps() {
  document.querySelectorAll("#agent-steps div").forEach((step) => {
    step.classList.remove("active", "done");
  });
}

function markAgentStep(name) {
  document.querySelectorAll("#agent-steps div").forEach((step) => {
    const isCurrent = step.dataset.step === name;
    if (isCurrent) step.classList.add("active");
    if (!isCurrent && step.classList.contains("active")) {
      step.classList.remove("active");
      step.classList.add("done");
    }
  });
}

function finishAgentSteps() {
  document.querySelectorAll("#agent-steps div").forEach((step) => {
    step.classList.remove("active");
    step.classList.add("done");
  });
}

function startProgress(id) {
  clearInterval(progressTimers[id]);
  const steps = progressSteps[id] || [["Starting", 10]];
  let index = 0;
  setProgress(id, steps[0][0], steps[0][1]);
  if (id === "ask") {
    resetAgentSteps();
    markAgentStep(steps[0][2]);
  }
  progressTimers[id] = window.setInterval(() => {
    index = Math.min(index + 1, steps.length - 1);
    const [message, percent, agentStep] = steps[index];
    setProgress(id, message, percent);
    if (id === "ask") markAgentStep(agentStep);
    if (index === steps.length - 1) {
      clearInterval(progressTimers[id]);
    }
  }, id === "ask" ? 420 : 360);
}

function completeProgress(id, message) {
  clearInterval(progressTimers[id]);
  setProgress(id, message, 100);
  if (id === "ask") finishAgentSteps();
}

function failProgress(id, message) {
  clearInterval(progressTimers[id]);
  setProgress(id, message, 100, "failed");
}

async function loadHealth() {
  try {
    await api("/health");
    $("#health").textContent = "Live";
    $("#health").className = "status ok";
  } catch {
    $("#health").textContent = "Offline";
    $("#health").className = "status bad";
  }
}

async function loadDocuments() {
  startProgress("source");
  const docs = await api("/api/documents");
  const container = $("#documents");
  container.innerHTML = "";
  if (!docs.length) {
    container.innerHTML = `<p>No sources indexed.</p>`;
    completeProgress("source", "No sources indexed yet");
    setGuide("source");
    return;
  }
  for (const doc of docs) {
    const item = document.createElement("div");
    item.className = "doc-item";
    item.innerHTML = `
      <strong>${escapeHtml(doc.title)}</strong>
      <span>${doc.chunk_count} chunks</span>
      <button type="button" data-id="${doc.id}" title="Delete source">Delete</button>
    `;
    item.querySelector("button").addEventListener("click", async () => {
      startProgress("source");
      try {
        await api(`/api/documents/${doc.id}`, { method: "DELETE" });
        toast("Source deleted");
        await loadDocuments();
      } catch (error) {
        failProgress("source", "Delete failed");
        toast(error.message);
      }
    });
    container.appendChild(item);
  }
  completeProgress("source", `${docs.length} source${docs.length === 1 ? "" : "s"} ready`);
  setGuide("ask");
}

async function loadSampleQuestions() {
  const questions = await api("/api/sample-questions");
  renderSampleQuestions(questions);
}

function renderSampleQuestions(questions) {
  const container = $("#sample-questions");
  container.innerHTML = "";
  if (!questions.length) {
    container.innerHTML = "<p>No sample questions available.</p>";
    return;
  }
  for (const question of questions) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "question-chip";
    chip.textContent = question;
    chip.addEventListener("click", () => {
      $("#question").value = question;
      setGuide("ask");
      $("#question").focus();
    });
    container.appendChild(chip);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderAnswer(result) {
  $("#answer").textContent = result.answer || "No answer returned.";
  $("#risk").textContent = `risk: ${result.hallucination_risk}`;
  $("#risk").className = `pill ${result.hallucination_risk}`;
  $("#score").textContent = `score: ${result.judge?.score ?? "n/a"}`;
  $("#score").className = `pill ${result.judge?.verdict || ""}`;
  $("#judge").textContent = JSON.stringify(result.judge || {}, null, 2);

  $("#citations").innerHTML =
    result.citations?.map((citation) => `
      <div class="citation">
        <strong>[${escapeHtml(citation.id)}] ${escapeHtml(citation.title)}</strong>
        <span>score ${citation.score}${citation.source_url ? ` | ${escapeHtml(citation.source_url)}` : ""}</span>
        <p>${escapeHtml(citation.snippet)}</p>
      </div>
    `).join("") || "<p>No citations.</p>";

  $("#claims").innerHTML =
    result.claims?.map((claim) => `
      <div class="claim" data-supported="${claim.supported}">
        <strong>${claim.supported ? "Supported" : "Needs review"}</strong>
        <p>${escapeHtml(claim.claim)}</p>
        <span>${escapeHtml((claim.citation_ids || []).join(", ") || claim.note || "")}</span>
      </div>
    `).join("") || "<p>No claims checked.</p>";

  $("#trace").innerHTML =
    result.trace?.map((entry) => `<div class="trace-item">${escapeHtml(entry)}</div>`).join("") || "<p>No trace.</p>";
}

$("#doc-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy) return;
  setBusy(true);
  startProgress("index");
  try {
    await api("/api/documents", {
      method: "POST",
      body: JSON.stringify({
        title: $("#doc-title").value,
        source_url: $("#doc-url").value || null,
        content: $("#doc-content").value,
      }),
    });
    event.target.reset();
    completeProgress("index", "Document indexed");
    toast("Source indexed");
    await loadDocuments();
    setGuide("ask");
  } catch (error) {
    failProgress("index", "Indexing failed");
    toast(error.message);
  } finally {
    setBusy(false);
  }
});

$("#upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("#file-input").files[0];
  if (!file) {
    toast("Choose a text file");
    return;
  }
  const form = new FormData();
  form.append("file", file);
  startProgress("upload");
  try {
    await api("/api/documents/upload", { method: "POST", body: form });
    $("#file-input").value = "";
    completeProgress("upload", "File indexed");
    toast("File indexed");
    await loadDocuments();
    setGuide("ask");
  } catch (error) {
    failProgress("upload", "Upload failed");
    toast(error.message);
  }
});

$("#load-demo").addEventListener("click", async () => {
  if (state.busy) return;
  setBusy(true);
  startProgress("demo");
  try {
    const result = await api("/api/demo/load", { method: "POST" });
    completeProgress("demo", `Demo ready: ${result.added} added, ${result.skipped} skipped`);
    renderSampleQuestions(result.sample_questions || []);
    toast("Demo data loaded");
    await loadDocuments();
    setGuide("ask");
  } catch (error) {
    failProgress("demo", "Demo load failed");
    toast(error.message);
  } finally {
    setBusy(false);
  }
});

$("#ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy) return;
  setBusy(true);
  setGuide("ask");
  startProgress("ask");
  $("#answer").textContent = "Running the guardrail, retriever, summarizer, critic, and judge agents...";
  try {
    const result = await api("/api/ask", {
      method: "POST",
      body: JSON.stringify({
        question: $("#question").value,
        top_k: Number($("#top-k").value || 6),
      }),
    });
    completeProgress("ask", "Agent run complete");
    renderAnswer(result);
    setGuide("verify");
  } catch (error) {
    failProgress("ask", "Agent run failed");
    toast(error.message);
    $("#answer").textContent = "The agent run failed.";
  } finally {
    setBusy(false);
  }
});

$("#refresh-docs").addEventListener("click", () => loadDocuments().catch((error) => {
  failProgress("source", "Refresh failed");
  toast(error.message);
}));

$("#refresh-questions").addEventListener("click", () => loadSampleQuestions().catch((error) => toast(error.message)));

$("#theme-toggle").addEventListener("click", () => {
  const current = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
  applyTheme(current === "dark" ? "light" : "dark");
});

applyTheme(localStorage.getItem("mak-theme") || "light");
loadHealth();
loadSampleQuestions().catch((error) => toast(error.message));
loadDocuments().catch((error) => {
  failProgress("source", "Refresh failed");
  toast(error.message);
});
