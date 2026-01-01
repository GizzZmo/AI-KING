const localKey = "ai_king_prompts";

const el = (id) => document.getElementById(id);
const catalogDefaults = window.defaultPromptCatalog || {
  presets: [],
  templates: [],
  prompts: [],
  settings: { theme: "cyberpunk", autosave: true },
};

let catalog = { ...catalogDefaults };

function hydrateCatalog(data) {
  catalog = {
    presets: data.presets || [],
    templates: data.templates || [],
    prompts: data.prompts || [],
    settings: data.settings || { theme: "cyberpunk", autosave: true },
  };
}

async function loadCatalog() {
  const fromLocal = localStorage.getItem(localKey);
  if (fromLocal) {
    try {
      hydrateCatalog(JSON.parse(fromLocal));
    } catch (err) {
      console.warn("Failed to parse local prompts", err);
    }
  }

  try {
    const res = await fetch("/api/prompts", { method: "GET" });
    if (res.ok) {
      const remote = await res.json();
      hydrateCatalog(remote);
    }
  } catch (err) {
    console.info("Offline or settings server unavailable, using local data.");
  }
}

function persistCatalog() {
  localStorage.setItem(localKey, JSON.stringify(catalog));
  fetch("/api/prompts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(catalog),
  }).catch(() => {
    console.info("Saved locally; backend settings server unreachable.");
  });
}

function renderSelect(selectEl, entries) {
  selectEl.innerHTML = "";
  entries.forEach((entry) => {
    const option = document.createElement("option");
    option.value = entry.id;
    option.textContent = entry.name;
    selectEl.appendChild(option);
  });
}

function renderPresetCards() {
  const list = el("preset-list");
  list.innerHTML = "";
  catalog.presets.forEach((preset) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h3>${preset.name}<span class="chip">Preset</span></h3>
      <p>${preset.prompt}</p>
    `;
    list.appendChild(card);
  });
}

function renderSaved() {
  const list = el("saved-list");
  list.innerHTML = "";
  catalog.prompts.forEach((prompt) => {
    const card = document.createElement("div");
    card.className = "card";
    const date = prompt.updated_at || "";
    card.innerHTML = `
      <h3>${prompt.name}<span class="chip">${prompt.template || "Custom"}</span></h3>
      <p>${prompt.content.slice(0, 140)}${prompt.content.length > 140 ? "..." : ""}</p>
      <p class="status"><span class="dot"></span>${date}</p>
    `;
    card.addEventListener("click", () => {
      el("prompt-name").value = prompt.name;
      el("prompt-input").value = prompt.content;
      if (prompt.template) el("template-select").value = prompt.template;
    });
    list.appendChild(card);
  });
}

function applyPreset() {
  const select = el("preset-select");
  const preset = catalog.presets.find((p) => p.id === select.value);
  if (!preset) return;
  el("prompt-input").value = preset.prompt;
  el("prompt-name").value = preset.name;
}

function applyTemplate() {
  const select = el("template-select");
  const template = catalog.templates.find((t) => t.id === select.value);
  if (!template) return;
  const name = el("prompt-name").value || "Mission";
  const body = template.body
    .replace("{objective}", name)
    .replace("{constraints}", "Safety first. Keep receipts.")
    .replace("{steps}", "- Research\n- Plan\n- Execute\n- Critique")
    .replace("{deliverables}", "Summary, traces, and next steps")
    .replace("{context}", "Latest notes")
    .replace("{criteria}", "Meets tests and roadmap")
    .replace("{tests}", "Unit coverage, manual checks")
    .replace("{positive}", "Clean logs")
    .replace("{issues}", "None detected")
    .replace("{actions}", "Ship and monitor");
  el("prompt-input").value = body;
}

function savePrompt() {
  const name = el("prompt-name").value || "Untitled";
  const content = el("prompt-input").value;
  if (!content.trim()) return;
  const template = el("template-select").value;
  const now = new Date().toISOString();
  const existing = catalog.prompts.find((p) => p.name === name);
  if (existing) {
    existing.content = content;
    existing.template = template;
    existing.updated_at = now;
  } else {
    catalog.prompts.unshift({
      id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      name,
      content,
      template,
      updated_at: now,
    });
  }
  persistCatalog();
  renderSaved();
}

function loadSavedFirst() {
  if (catalog.prompts.length === 0) return;
  const prompt = catalog.prompts[0];
  el("prompt-name").value = prompt.name;
  el("prompt-input").value = prompt.content;
  if (prompt.template) el("template-select").value = prompt.template;
}

function clearCurrent() {
  el("prompt-name").value = "";
  el("prompt-input").value = "";
}

function downloadPrompts() {
  const blob = new Blob([JSON.stringify(catalog, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ai-king-prompts.json";
  link.click();
  URL.revokeObjectURL(url);
}

async function main() {
  hydrateCatalog(catalogDefaults);
  await loadCatalog();
  renderSelect(el("preset-select"), catalog.presets);
  renderSelect(el("template-select"), catalog.templates);
  renderPresetCards();
  renderSaved();
  loadSavedFirst();

  el("apply-preset").addEventListener("click", applyPreset);
  el("apply-template").addEventListener("click", applyTemplate);
  el("save-prompt").addEventListener("click", savePrompt);
  el("load-saved").addEventListener("click", loadSavedFirst);
  el("clear-current").addEventListener("click", clearCurrent);
  el("download-prompts").addEventListener("click", downloadPrompts);
}

document.addEventListener("DOMContentLoaded", main);
