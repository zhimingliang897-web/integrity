const state = {
  providers: [],
  results: [],
  loading: false
};

const elements = {
  providerList: document.getElementById("providerList"),
  resultGrid: document.getElementById("resultGrid"),
  resultHint: document.getElementById("resultHint"),
  providerHint: document.getElementById("providerHint"),
  question: document.getElementById("question"),
  systemPrompt: document.getElementById("systemPrompt"),
  temperature: document.getElementById("temperature"),
  runCompare: document.getElementById("runCompare"),
  refreshProviders: document.getElementById("refreshProviders"),
  selectAll: document.getElementById("selectAll"),
  deselectAll: document.getElementById("deselectAll"),
  saveResults: document.getElementById("saveResults")
};

function loadLocalSettings() {
  const raw = localStorage.getItem("providerSettings");
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function saveLocalSettings(settings) {
  localStorage.setItem("providerSettings", JSON.stringify(settings));
}

function mergeProviders(list, settings) {
  return list.map(provider => {
    const saved = settings[provider.name] || {};
    const remoteModels = Array.isArray(provider.models) ? provider.models : [];
    const localModels = Array.isArray(saved.customModels) ? saved.customModels : [];
    const enabledModels = Array.isArray(saved.enabledModels) ? saved.enabledModels : (remoteModels.length > 0 ? [remoteModels[0]] : []);

    return {
      ...provider,
      baseUrl: saved.baseUrl ?? provider.baseUrl ?? "",
      customModels: localModels,
      enabledModels: enabledModels,
      allModels: [...new Set([...remoteModels, ...localModels])]
    };
  });
}

async function fetchProviders() {
  elements.providerHint.textContent = "加载中...";
  try {
    const response = await fetch("/api/providers");
    const data = await response.json();
    const settings = loadLocalSettings();
    state.providers = mergeProviders(data.providers || [], settings);
    elements.providerHint.textContent = "";
    renderProviders();
  } catch (err) {
    elements.providerHint.textContent = "加载失败";
    console.error(err);
  }
}

function updateSetting(name, patch) {
  const settings = loadLocalSettings();
  settings[name] = { ...(settings[name] || {}), ...patch };
  saveLocalSettings(settings);
}

function renderProviders() {
  elements.providerList.innerHTML = "";
  if (!state.providers.length) {
    elements.providerList.innerHTML = `<div class="empty">未找到供应商，请检查 API.md</div>`;
    return;
  }

  state.providers.forEach((provider, pIndex) => {
    const card = document.createElement("div");
    card.className = "provider-card";

    const header = document.createElement("div");
    header.className = "provider-header";

    const titleGroup = document.createElement("div");
    titleGroup.className = "title-group";

    const title = document.createElement("div");
    title.className = "provider-title";
    title.textContent = provider.name;

    const badge = document.createElement("span");
    badge.className = provider.keyPresent ? "badge ok" : "badge warn";
    badge.textContent = provider.keyPresent ? "已读取 Key" : "未读取 Key";

    titleGroup.appendChild(title);
    titleGroup.appendChild(badge);

    header.appendChild(titleGroup);

    const urlField = document.createElement("div");
    urlField.className = "field";
    const urlInput = document.createElement("input");
    urlInput.value = provider.baseUrl || "";
    urlInput.placeholder = "Base URL (e.g. https://api.xxx.com/v1)";
    urlInput.addEventListener("input", () => {
      provider.baseUrl = urlInput.value.trim();
      updateSetting(provider.name, { baseUrl: provider.baseUrl });
    });
    urlField.appendChild(urlInput);

    const modelsContainer = document.createElement("div");
    modelsContainer.className = "models-container";

    provider.allModels.forEach(model => {
      const modelItem = document.createElement("label");
      modelItem.className = "model-item";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = provider.enabledModels.includes(model);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          if (!provider.enabledModels.includes(model)) provider.enabledModels.push(model);
        } else {
          provider.enabledModels = provider.enabledModels.filter(m => m !== model);
        }
        updateSetting(provider.name, { enabledModels: provider.enabledModels });
      });

      const span = document.createElement("span");
      span.textContent = model;

      const queryBtn = document.createElement("button");
      queryBtn.textContent = "提问";
      queryBtn.className = "ghost small query-btn";
      queryBtn.addEventListener("click", (e) => {
        e.preventDefault();
        runSingleQuery(provider.name, model, provider.baseUrl);
      });

      modelItem.appendChild(checkbox);
      modelItem.appendChild(span);
      modelItem.appendChild(queryBtn);
      modelsContainer.appendChild(modelItem);
    });

    const addModelContainer = document.createElement("div");
    addModelContainer.className = "add-model-container";
    const addInput = document.createElement("input");
    addInput.placeholder = "添加新模型...";
    const addBtn = document.createElement("button");
    addBtn.textContent = "+";
    addBtn.className = "ghost small";
    addBtn.addEventListener("click", () => {
      const newModel = addInput.value.trim();
      if (newModel && !provider.allModels.includes(newModel)) {
        provider.customModels.push(newModel);
        provider.allModels.push(newModel);
        provider.enabledModels.push(newModel);
        updateSetting(provider.name, {
          customModels: provider.customModels,
          enabledModels: provider.enabledModels
        });
        renderProviders();
      }
    });
    addModelContainer.appendChild(addInput);
    addModelContainer.appendChild(addBtn);

    card.appendChild(header);
    card.appendChild(urlField);
    card.appendChild(modelsContainer);
    card.appendChild(addModelContainer);
    elements.providerList.appendChild(card);
  });
}

function renderResults() {
  elements.resultGrid.innerHTML = "";
  if (!state.results.length) {
    elements.resultGrid.innerHTML = `<div class="empty">暂无结果</div>`;
    return;
  }

  state.results.forEach(result => {
    const card = document.createElement("div");
    card.className = "result-card";

    const header = document.createElement("div");
    header.className = "result-header";

    const title = document.createElement("div");
    title.className = "result-title";
    title.textContent = `${result.name} · ${result.model || "-"}`;

    const meta = document.createElement("div");
    meta.className = "result-meta";

    const rerunBtn = document.createElement("button");
    rerunBtn.textContent = "重跑";
    rerunBtn.className = "ghost small query-btn";
    rerunBtn.addEventListener("click", () => {
      runSingleQuery(result.name, result.model, result.baseUrl);
    });

    meta.appendChild(rerunBtn);

    const latency = document.createElement("span");
    latency.textContent = result.latencyMs ? `${result.latencyMs} ms` : "";
    meta.appendChild(latency);

    header.appendChild(title);
    header.appendChild(meta);

    const body = document.createElement("pre");
    body.className = result.error ? "result-body error" : "result-body";
    body.textContent = result.error || result.content || "";

    card.appendChild(header);
    card.appendChild(body);
    elements.resultGrid.appendChild(card);
  });
}

async function runCompare() {
  const requests = [];
  state.providers.forEach(p => {
    p.enabledModels.forEach(model => {
      requests.push({
        name: p.name,
        model: model,
        baseUrl: p.baseUrl
      });
    });
  });
  executeCompare(requests);
}

async function runSingleQuery(name, model, baseUrl) {
  executeCompare([{
    name,
    model,
    baseUrl
  }]);
}

async function executeCompare(requests) {
  if (state.loading) return;
  const question = elements.question.value.trim();
  const systemPrompt = elements.systemPrompt.value.trim();
  const temperature = Number(elements.temperature.value);

  if (!question) {
    elements.resultHint.textContent = "请先填写问题";
    return;
  }

  if (!requests.length) {
    elements.resultHint.textContent = "请至少选择一个模型";
    return;
  }

  elements.resultHint.textContent = "请求中...";
  state.loading = true;
  elements.runCompare.disabled = true;

  const payload = {
    question,
    systemPrompt,
    temperature: Number.isFinite(temperature) ? temperature : undefined,
    requests: requests
  };

  try {
    const response = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      state.results = [];
      elements.resultHint.textContent = data.error || "请求失败";
      renderResults();
    } else {
      state.results = data.results || [];
      elements.resultHint.textContent = "";
      renderResults();
    }
  } catch (err) {
    elements.resultHint.textContent = "服务连接失败";
    console.error(err);
  } finally {
    state.loading = false;
    elements.runCompare.disabled = false;
  }
}

function getResultsAsMarkdown() {
  const question = elements.question.value.trim();
  const systemPrompt = elements.systemPrompt.value.trim();

  let markdown = "# AI 模型对比结果\n\n";
  markdown += "**问题：** " + question + "\n\n";
  if (systemPrompt) {
    markdown += "**系统提示词：** " + systemPrompt + "\n\n";
  }
  markdown += "--- \n\n";

  state.results.forEach(result => {
    markdown += "## " + result.name + " - " + result.model + "\n\n";
    if (result.error) {
      markdown += "**错误：**\n```\n" + result.error + "\n```\n\n";
    } else {
      markdown += "**延迟：** " + result.latencyMs + " ms\n\n";
      markdown += "**回复：**\n```markdown\n" + result.content + "\n```\n\n";
    }
    markdown += "--- \n\n";
  });

  return markdown;
}

function saveResults() {
  if (!state.results.length) {
    alert("没有可导出的结果。");
    return;
  }

  const markdown = getResultsAsMarkdown();
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ai-compare-${Date.now()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

elements.runCompare.addEventListener("click", runCompare);
elements.refreshProviders.addEventListener("click", fetchProviders);

elements.selectAll.addEventListener("click", () => {
  state.providers.forEach(p => {
    p.enabledModels = [...p.allModels];
    updateSetting(p.name, { enabledModels: p.enabledModels });
  });
  renderProviders();
});

elements.deselectAll.addEventListener("click", () => {
  state.providers.forEach(p => {
    p.enabledModels = [];
    updateSetting(p.name, { enabledModels: p.enabledModels });
  });
  renderProviders();
});

elements.saveResults.addEventListener("click", saveResults);

fetchProviders();
